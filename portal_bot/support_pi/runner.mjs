import { Agent } from '@earendil-works/pi-agent-core';
import { streamSimple } from '@earendil-works/pi-ai/api/openai-completions';
import { createInterface } from 'node:readline';

// One disposable agent per case turn. Only explicitly supplied case tools exist.
const lines = createInterface({ input: process.stdin });
const input = lines[Symbol.asyncIterator]();
const send = (value) => process.stdout.write(JSON.stringify(value) + '\n');
const read = async () => {
  const line = await input.next();
  if (line.done) throw new Error('bridge_closed');
  return JSON.parse(line.value);
};

try {
  const init = await read();
  const model = {
    id: init.model, name: init.model, api: 'openai-completions',
    provider: 'openrouter', baseUrl: 'https://openrouter.ai/api/v1',
    reasoning: true, input: ['text'], contextWindow: 1000000, maxTokens: 65536,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  };
  let turns = 0;
  let calls = 0;
  let providerStarted = 0;
  let latencyMs = 0;
  const usage = { prompt_tokens: 0, completion_tokens: 0, cached_tokens: 0 };
  const agent = new Agent({
    initialState: {
      model, thinkingLevel: 'high', systemPrompt: init.prompt,
      tools: init.tools.map((tool) => ({
        ...tool, label: tool.name,
        async execute(id, args) {
          if (++calls > 12) throw new Error('tool_budget');
          send({ type: 'tool', name: tool.name, args });
          const result = await read();
          return { content: [{ type: 'text', text: JSON.stringify(result) }], details: {} };
        },
      })),
    },
    toolExecution: 'sequential',
    getApiKey: () => init.api_key,
    streamFn: (model, context, options) => {
      providerStarted = performance.now();
      return streamSimple(model, context, { ...options, maxRetries: 0 });
    },
    onPayload(payload) {
      delete payload.max_tokens;
      delete payload.max_completion_tokens;
      payload.reasoning = { effort: 'high' };
      payload.provider = { require_parameters: true, data_collection: 'allow' };
      // Reasoning may accompany tool calls; keep it in transient pi memory only.
      if (JSON.stringify(payload).length > init.context_chars) throw new Error('context_budget');
      if (++turns > 6) throw new Error('turn_budget');
      // Reserve the last model turn for a final answer after the collected tool results.
      if (turns === 6 || calls >= 12) payload.tool_choice = 'none';
    },
    shouldStopAfterTurn: () => turns >= 6,
  });
  agent.subscribe((event) => {
    if (event.type === 'message_end' && event.message.role === 'assistant') {
      latencyMs += performance.now() - providerStarted;
      const current = event.message.usage;
      usage.prompt_tokens += current.input + current.cacheRead + current.cacheWrite;
      usage.completion_tokens += current.output;
      usage.cached_tokens += current.cacheRead;
    }
  });
  const timer = setTimeout(() => agent.abort(), init.timeout_ms);
  try {
    await agent.prompt(init.question);
    const last = agent.state.messages.at(-1);
    if (last?.role !== 'assistant' || last.stopReason !== 'stop') {
      send({ type: 'error', code: last?.stopReason === 'error' ? 'provider_error' : 'incomplete', turns, calls });
      process.exitCode = 1;
    } else {
      const reply = last.content.filter((item) => item.type === 'text').map((item) => item.text).join('');
      if (!reply || reply.length > 16000) throw new Error('invalid_reply');
      send({ type: 'done', content: reply, turns, calls, usage, latency_ms: Math.round(latencyMs) });
    }
  } finally {
    clearTimeout(timer);
  }
} catch (error) {
  // Provider error bodies and private reasoning must never enter process logs.
  const safeCodes = new Set(['context_budget', 'turn_budget', 'invalid_reply', 'bridge_closed']);
  send({ type: 'error', code: safeCodes.has(error?.message) ? error.message : 'support_pi_failed' });
  process.exitCode = 1;
} finally {
  lines.close();
}
