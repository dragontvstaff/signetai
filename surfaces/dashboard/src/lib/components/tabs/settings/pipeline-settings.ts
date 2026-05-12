import {
	DEFAULT_PIPELINE_TIMEOUT_MS,
	type PipelineProviderChoice,
	defaultPipelineModel,
	isPipelineProvider,
} from "@signet/core/pipeline-providers";

function toRecord(value: unknown): Record<string, unknown> | null {
	return typeof value === "object" && value !== null && !Array.isArray(value)
		? Object.fromEntries(Object.entries(value))
		: null;
}

function mutableRecord(value: unknown): Record<string, unknown> | null {
	return typeof value === "object" && value !== null && !Array.isArray(value)
		? (value as Record<string, unknown>)
		: null;
}

function ensureRecord(root: Record<string, unknown>, key: string): Record<string, unknown> {
	const existing = mutableRecord(root[key]);
	if (existing) return existing;
	const next: Record<string, unknown> = {};
	root[key] = next;
	return next;
}

function readPipeline(agent: unknown): Record<string, unknown> | null {
	const root = toRecord(agent);
	const mem = toRecord(root?.memory);
	return toRecord(mem?.pipelineV2);
}

function readString(root: Record<string, unknown> | null, ...path: string[]): string | undefined {
	let node: unknown = root;
	for (const part of path) {
		const record = toRecord(node);
		if (!record) return undefined;
		node = record[part];
	}
	return typeof node === "string" && node.trim().length > 0 ? node : undefined;
}

function readNumber(root: Record<string, unknown> | null, ...path: string[]): number | undefined {
	let node: unknown = root;
	for (const part of path) {
		const record = toRecord(node);
		if (!record) return undefined;
		node = record[part];
	}
	return typeof node === "number" && Number.isFinite(node) ? node : undefined;
}

function readBoolean(root: Record<string, unknown> | null, ...path: string[]): boolean | undefined {
	let node: unknown = root;
	for (const part of path) {
		const record = toRecord(node);
		if (!record) return undefined;
		node = record[part];
	}
	return typeof node === "boolean" ? node : undefined;
}

export function hasExplicitSynthesisConfig(agent: unknown): boolean {
	return toRecord(readPipeline(agent)?.synthesis) !== null;
}

export function hasExplicitSynthesisProvider(agent: unknown): boolean {
	const pipeline = readPipeline(agent);
	return isPipelineProvider(readString(pipeline, "synthesis", "provider"));
}

export function resolveSynthesisProvider(agent: unknown): PipelineProviderChoice {
	const pipeline = readPipeline(agent);
	const explicit = readString(pipeline, "synthesis", "provider");
	if (isPipelineProvider(explicit)) return explicit;
	const flat = readString(pipeline, "extractionProvider");
	if (isPipelineProvider(flat)) return flat;
	const nested = readString(pipeline, "extraction", "provider");
	if (isPipelineProvider(nested)) return nested;
	return "llama-cpp";
}

export function resolveSynthesisModel(agent: unknown): string {
	const pipeline = readPipeline(agent);
	const provider = resolveSynthesisProvider(agent);
	const explicit = readString(pipeline, "synthesis", "model");
	if (explicit) return explicit;
	if (hasExplicitSynthesisProvider(agent)) return defaultPipelineModel(provider);
	return (
		readString(pipeline, "extractionModel") ??
		readString(pipeline, "extraction", "model") ??
		defaultPipelineModel(provider)
	);
}

export function resolveSynthesisEndpoint(agent: unknown): string {
	const pipeline = readPipeline(agent);
	const explicit = readString(pipeline, "synthesis", "endpoint") ?? readString(pipeline, "synthesis", "base_url");
	if (explicit) return explicit;
	if (hasExplicitSynthesisProvider(agent)) return "";
	return (
		readString(pipeline, "extraction", "endpoint") ??
		readString(pipeline, "extraction", "base_url") ??
		readString(pipeline, "extractionEndpoint") ??
		readString(pipeline, "extractionBaseUrl") ??
		""
	);
}

export function resolveSynthesisTimeout(agent: unknown): number {
	const pipeline = readPipeline(agent);
	const explicit = readNumber(pipeline, "synthesis", "timeout");
	if (explicit !== undefined) return explicit;
	if (hasExplicitSynthesisProvider(agent)) return 120000;
	return (
		readNumber(pipeline, "extraction", "timeout") ??
		readNumber(pipeline, "extractionTimeout") ??
		DEFAULT_PIPELINE_TIMEOUT_MS
	);
}

export function resolveSynthesisEnabled(agent: unknown): boolean {
	const pipeline = readPipeline(agent);
	if (resolveSynthesisProvider(agent) === "none") return false;
	return readBoolean(pipeline, "synthesis", "enabled") ?? true;
}
export function applyRecommendedPipelineSetup(
	agentConfig: Record<string, unknown>,
	options: { readonly provider?: PipelineProviderChoice; readonly model?: string } = {},
): void {
	const provider = options.provider ?? "acpx";
	const model = options.model?.trim() || defaultPipelineModel(provider);
	const memory = ensureRecord(agentConfig, "memory");
	const pipeline = ensureRecord(memory, "pipelineV2");
	pipeline.enabled = provider !== "none";
	pipeline.extractionProvider = provider;
	pipeline.extractionModel = model;
	pipeline.semanticContradictionEnabled = provider !== "none";
	pipeline.graphEnabled = provider !== "none";
	pipeline.rerankerEnabled = provider !== "none";
	pipeline.synthesis = {
		enabled: provider !== "none",
		provider,
		model,
		timeout: 120000,
	};
}
