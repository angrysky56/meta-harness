# Domain Spec: <domain name>

## 1. Problem framing

- **Goal**: <What are we improving?>
- **Unit of evaluation**: <Episode/Task/Conversation>
- **Fixed**: Base Model, Datasets
- **Variable**: Harness Code (Memory, Retrieval, Prompting)
- **Base Model**: <e.g., Llama-3-8B>
- **Budget**: <e.g., 20 iterations, 3 candidates per iter>

## 2. Harness definition

- **Interface**: `class MemorySystem(Protocol): ...`
- **Base Class**: `agents/base.py`
- **Validation**: `pytest tests/test_harness.py`

## 3. Evaluation

- **Search Set**: <e.g., 5 validation datasets>
- **Held-out Test**: <e.g., 2 hidden datasets>
- **Primary Metric**: Accuracy (%)
- **Secondary Metrics**: Latency, Token Count
- **Noise Level**: <Low/Medium/High>
- **Duration**: <seconds per eval>

## 4. Baselines

- **Baselines**: `no_memory`, `fewshot_memory`
- **Strongest Current**: `fewshot_all`
- **Helpers**: `utils.retrieve_k`, `utils.summarize_context`

## 5. Offline experience

- **Traces**: <Link to any existing traces>
- **Domain Docs**: <Ingest into Synapse>

## 6. Online experience

- **Logging**: `logs/raw_traces.jsonl`
- **Artifacts**: `agents/*.py`, `logs/val.json`
- **Metadata**: model_id, timestamp, cost
- **CLI**: `python meta_harness.py --status`
