import { pipeline } from '@huggingface/transformers';

type Embedder = (
  text: string[],
  options: { pooling: 'mean'; normalize: true },
) => Promise<{ tolist(): number[][] }>;

let embedder: Embedder | null = null;
let activeMode: 'semantic-webgpu' | 'semantic-wasm' = 'semantic-wasm';

async function loadEmbedder(): Promise<Embedder> {
  if (embedder) return embedder;
  try {
    embedder = await pipeline(
      'feature-extraction',
      'Xenova/multilingual-e5-small',
      { device: 'webgpu', dtype: 'q8' },
    ) as unknown as Embedder;
    activeMode = 'semantic-webgpu';
  } catch {
    embedder = await pipeline(
      'feature-extraction',
      'Xenova/multilingual-e5-small',
      { device: 'wasm', dtype: 'q8' },
    ) as unknown as Embedder;
    activeMode = 'semantic-wasm';
  }
  return embedder;
}

function cosine(left: number[], right: number[]): number {
  let dot = 0;
  let leftNorm = 0;
  let rightNorm = 0;
  for (let index = 0; index < left.length; index += 1) {
    dot += left[index] * right[index];
    leftNorm += left[index] ** 2;
    rightNorm += right[index] ** 2;
  }
  return dot / (Math.sqrt(leftNorm) * Math.sqrt(rightNorm) || 1);
}

self.onmessage = async (event: MessageEvent<{
  requestId: string;
  answer: string;
  evidence: Array<{ id: string; text: string }>;
}>) => {
  const { requestId, answer, evidence } = event.data;
  try {
    const model = await loadEmbedder();
    const output = await model(
      [`query: ${answer}`, ...evidence.map((item) => `passage: ${item.text}`)],
      { pooling: 'mean', normalize: true },
    );
    const vectors = output.tolist();
    const scores = evidence
      .map((item, index) => ({ id: item.id, score: cosine(vectors[0], vectors[index + 1]) }))
      .sort((left, right) => right.score - left.score);
    self.postMessage({ requestId, ok: true, mode: activeMode, scores });
  } catch (error) {
    self.postMessage({
      requestId,
      ok: false,
      message: error instanceof Error ? error.message : 'Semantic model unavailable',
    });
  }
};
