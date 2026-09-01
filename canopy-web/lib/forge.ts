import type { ForgeStage } from './canopy-types';
import { unicodeTokens } from './diagnosis';

const STOP = new Set([
  'the', 'and', 'that', 'with', 'from', 'this', 'have', 'into', 'your', 'when',
  'care', 'este', 'sunt', 'pentru', 'care', 'porque', 'para', 'dans', 'eine',
]);

export function forgeStages(notes: string): ForgeStage[] {
  const sentences = notes
    .split(/(?<=[.!?。！？])\s+/u)
    .map((sentence) => sentence.trim())
    .filter(Boolean);
  const counts = new Map<string, number>();
  unicodeTokens(notes).forEach((token) => {
    if (token.length < 3 || STOP.has(token)) return;
    counts.set(token, (counts.get(token) ?? 0) + 1);
  });
  const concepts = [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]))
    .slice(0, 6)
    .map(([term]) => term);
  while (concepts.length < 6) concepts.push(`concept ${concepts.length + 1}`);
  const labels = ['Notice', 'Connect', 'Model', 'Test', 'Transfer', 'Teach back'];
  return labels.map((label, index) => {
    const concept = concepts[index];
    const evidence = sentences.find((sentence) =>
      sentence.toLocaleLowerCase().includes(concept.toLocaleLowerCase()),
    ) ?? sentences[index % Math.max(1, sentences.length)] ?? notes.slice(0, 180);
    return {
      id: `forge-${index + 1}`,
      label,
      concept,
      question: index < 4
        ? `How does ${concept} change the explanation, and what evidence supports that relationship?`
        : index === 4
          ? `Where would ${concept} behave differently in a new context?`
          : `How would you teach ${concept} without hiding its limits?`,
      evidence,
    };
  });
}
