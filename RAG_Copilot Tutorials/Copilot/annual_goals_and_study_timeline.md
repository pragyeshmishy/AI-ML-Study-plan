# Annual Goals & Study Timeline — Senior ML Engineer

**Review Period:** 2026
**Role:** Senior ML Engineer
**Focus:** Production excellence, platform-level impact, and technical leadership in AI/ML systems

---

## At a Glance

### Annual Goals

| # | Goal Area | Key Outcome | Success Looks Like |
|---|-----------|-------------|-------------------|
| 1 | Production Excellence — Smart Scheduler | Stable production system with business KPIs | Beta → GA, SLAs defined, monitoring live, cost optimized |
| 2 | LLM/RAG Systems — Technical Depth | Eval framework + advanced retrieval in production | RAGAS pipeline running, 2+ RAG algorithms benchmarked, re-ranking integrated |
| 3 | Infrastructure & Data Ownership | End-to-end IaC + data transformation | Terraform CI/CD, dbt project with tests, zero manual infra changes |
| 4 | Platform Thinking — Reusable Frameworks | Components other teams can adopt | Shared eval library, Terraform modules, internal best-practices doc |
| 5 | Cross-Team Collaboration | Business use cases driven end-to-end | 1+ new use case scoped with stakeholders, results presented to leadership |
| 6 | Technical Leadership | Team capability multiplier | 2+ knowledge shares, 1+ engineer mentored, engineering standards proposed |
| 7 | Continuous Technical Growth | Structured depth across 5 areas | Tangible artifact per area (code, benchmark, doc, or deployed infra) |

### Study Plan

| Phase | Topics | Weeks | Hours | Key Artifact |
|-------|--------|-------|-------|-------------|
| 1 | LLM/RAG Evaluation | Weeks 1-4 | ~30h | End-to-end eval pipeline + LangSmith tracing |
| 2 | Advanced RAG Algorithms | Weeks 5-8 | ~32h | 4+ algorithms prototyped and benchmarked |
| 3 | Re-Ranking Methods | Weeks 9-10 | ~15h | Re-ranking integrated with latency/quality report |
| 4 | dbt on AWS | Weeks 11-12 | ~12h | dbt project running on Snowflake with tests passing |
| 5 | Terraform | Weeks 13-16 | ~28h | DC-Copilot infra fully in Terraform + CI/CD |
| 6 | Integration & Mock Interviews | Weeks 17-18 | ~15h | Can whiteboard all topics at senior level |
| | **Total** | **~18 weeks** | **~132h** | **~10h/week (1-1.5h weekdays + 2-3h weekends)** |

---

## 1. Production Excellence — Smart Scheduler

**Objective:** Deliver Smart Scheduler as a stable, production-grade system with measurable business impact.

- Transition Smart Scheduler from beta to full production release with defined SLAs (availability, latency, error rate)
- Establish production monitoring and alerting (latency P50/P95/P99, error budgets, throughput dashboards) to ensure system reliability meets enterprise standards
- Define and track key business KPIs tied to Smart Scheduler (e.g., scheduling accuracy improvement, reduction in manual scheduling effort, time-to-resolution)
- Conduct load testing and capacity planning to validate system behavior under peak traffic conditions
- Implement cost tracking per inference call and optimize resource utilization to reduce per-request cost by a measurable margin
- Own the full incident response lifecycle — root cause analysis, remediation, and post-mortem documentation for any production issues
- Deliver a production readiness review document covering observability, failover, data integrity, and rollback procedures

## 2. LLM/RAG Systems — Technical Depth & Innovation

**Objective:** Establish deep, demonstrable expertise in LLM evaluation and advanced retrieval systems, applied directly to production workloads.

- Design and implement a comprehensive RAG evaluation framework covering retrieval quality (Context Precision, Recall, MRR, NDCG), generation quality (Faithfulness, Answer Relevancy, BERTScore), and end-to-end correctness (RAGAS suite, LLM-as-a-Judge)
- Evaluate and integrate at least two advanced RAG algorithms (e.g., Hybrid Search, Corrective RAG, RAG Fusion) into production retrieval pipelines with before/after benchmarks
- Implement a re-ranking layer (Cross-Encoder or equivalent) and measure its impact on retrieval precision and downstream answer quality
- Build automated regression detection for RAG quality — drift monitoring that flags degradation across evaluation metrics week-over-week
- Produce an internal technical document or knowledge-share on "Advanced RAG Patterns: What Works and What Doesn't" based on hands-on experimentation

## 3. Infrastructure & Data Ownership

**Objective:** Own the infrastructure and data transformation layer end-to-end, ensuring reproducibility, auditability, and operational maturity.

- Define and manage all application infrastructure using Terraform — covering compute (ECS/Fargate), networking (VPC, security groups), storage (S3, DynamoDB), secrets (Secrets Manager, Parameter Store), and AI services (OpenSearch Serverless)
- Implement Terraform CI/CD integration with automated `plan` on pull requests and controlled `apply` on merge, including security scanning (tflint, checkov)
- Build and maintain a dbt project for data transformation — staging models, tested marts, incremental materializations — integrated with Snowflake on AWS
- Establish data quality gates using dbt tests (schema validation, referential integrity, freshness checks) as part of the data pipeline
- Ensure all infrastructure changes are peer-reviewed, version-controlled, and auditable — no manual console changes in production environments

## 4. Platform Thinking — Reusable Frameworks & Components

**Objective:** Move beyond project-level delivery to build reusable components that accelerate the team and adjacent teams.

- Extract and package the RAG evaluation framework as a reusable internal library or shared service that other teams can adopt for their own LLM workloads
- Design a standardized LLM observability stack (tracing, token usage tracking, latency breakdowns per pipeline node) that can be adopted across multiple AI applications
- Create Terraform modules for common AI/ML infrastructure patterns (vector database setup, LLM serving infra, async processing queues) that reduce setup time for new projects
- Document and publish internal best practices for production LLM systems — covering evaluation, retrieval, re-ranking, monitoring, and cost management
- Identify at least one opportunity to generalize a DC-Copilot component into a shared capability (e.g., intent classification service, document ingestion pipeline, streaming response framework)

## 5. Cross-Team Collaboration & Business Impact

**Objective:** Drive end-to-end business use cases by partnering with product, operations, and engineering teams beyond the immediate ML team.

- Partner with at least one business stakeholder team to identify and scope a new use case for the Smart Scheduler or DC-Copilot platform — from problem definition through deployment
- Lead technical design discussions with cross-functional teams, translating business requirements into measurable ML system specifications
- Present Smart Scheduler production results (business KPIs, system performance, lessons learned) to engineering leadership and non-technical stakeholders
- Actively participate in architecture reviews for adjacent systems where ML/AI integration is being considered — provide technical guidance on feasibility, tradeoffs, and recommended patterns
- Establish a feedback loop with end users (e.g., maintenance technicians, operations managers) to inform model improvements and feature prioritization

## 6. Technical Leadership & Knowledge Multiplication

**Objective:** Operate as a technical multiplier — elevating the team's capabilities, not just individual output.

- Conduct at least two internal knowledge-sharing sessions (lunch-and-learn, tech talk, or written deep-dive) on topics such as RAG evaluation, Terraform patterns, or production LLM operations
- Mentor at least one junior or mid-level engineer through a technical project — provide guidance on system design, code quality, and production readiness
- Contribute to the team's engineering standards by proposing and documenting at least one new standard or convention (e.g., evaluation baseline requirements, infrastructure-as-code policy, LLM safety checklist)
- Participate in on-call rotations and lead incident response for ML systems, building team-wide operational maturity
- Proactively identify technical debt or reliability risks in existing systems and propose prioritized remediation plans with clear business justification

## 7. Continuous Technical Growth

**Objective:** Deepen expertise in areas that directly enhance the quality and scope of delivered work.

- Complete structured study across five technical areas, with hands-on implementation tied to production systems:

| Area | Scope | Application |
|------|-------|-------------|
| LLM/RAG Evaluation | RAGAS, BERTScore, G-Eval, LLM-as-Judge, Drift Detection | Eval framework for DC-Copilot and Smart Scheduler |
| Advanced RAG | Hybrid Search, CRAG, Graph RAG, RAG Fusion, Agentic RAG | Retrieval quality improvements in production |
| Re-Ranking | Cross-Encoder, Cohere Rerank, RRF, FlashRank | Precision gains in document retrieval |
| dbt on AWS | Models, tests, incremental materializations, Snowflake | Data transformation and quality for analytics |
| Terraform | Modules, remote state, CI/CD, AWS provider (IAM, VPC, ECS) | Full infrastructure ownership |

- Each area concludes with a tangible artifact: working code, benchmark report, internal doc, or deployed infrastructure
- Share key learnings with the broader team through documentation or presentations — ensuring growth translates into team capability

---

> **Note:** These goals are designed to reflect end-to-end ownership, measurable business outcomes, and technical leadership at a level that drives organizational impact beyond individual projects.

---
---

# Study Timeline & Gap Closure Plan

**Goal:** Master LLM Evaluation, Advanced RAG, Re-Ranking, DBT, and Terraform
**Source:** minibook_llm_rag_evaluation_dbt.md + Terraform (external)
**Baseline:** Working knowledge of Python, ML fundamentals, AWS, and basic RAG (built DC-Copilot)
**Daily budget:** 1-1.5 hours on weekdays, ~2-3 hours on weekends

---

## Summary

| Phase | Topics | Weeks | Hours |
|-------|--------|-------|-------|
| 1 | LLM/RAG Evaluation Metrics | 4 weeks | ~30h |
| 2 | Advanced RAG Algorithms | 4 weeks | ~32h |
| 3 | Re-Ranking Methods | 2 weeks | ~15h |
| 4 | DBT (Data Build Tool) on AWS | 2 weeks | ~12h |
| 5 | Terraform (IaC) | 4 weeks | ~28h |
| 6 | Integration & Mock Interviews | 2 weeks | ~15h |
| **Total** | | **~18 weeks (~4.5 months)** | **~132h** |

> Pace: ~1h weekdays (5h/week) + ~2.5h weekends (5h/week) = **~10h/week**
> This is realistic alongside a full-time job.

---

## Phase 1: LLM & RAG Evaluation (Weeks 1-4, ~30h)

### Weeks 1-2 — Classical & Embedding-Based Metrics

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W1-D1 | Why Eval Matters (1.1) | Read section, note DC-Copilot's current gaps | 1h |
| W1-D2 | Eval Taxonomy (1.2) | Map 3 layers (Retrieval/Generation/E2E) to DC-Copilot | 1h |
| W1-D3 | BLEU (1.3) | Read theory + run `nltk` example | 1h |
| W1-D4 | ROUGE (1.4) | Run `rouge-score` on DC-Copilot outputs | 1h |
| W1-D5 | BLEU vs ROUGE | Compare scores on same response pairs, write notes | 1h |
| W1-WE | METEOR (1.5) + BERTScore (1.6) | Hands-on: compare all 4 metrics on 5 DC-Copilot responses | 2.5h |
| W2-D1 | Perplexity (1.7) | Read theory, understand when it applies | 1h |
| W2-D2 | RAGAS Framework (1.8) | Install RAGAS, run first `evaluate()` call | 1h |
| W2-D3 | Faithfulness (1.9) | Create test cases with known hallucinations, run RAGAS | 1h |
| W2-D4 | Answer Relevancy (1.10) | Test on DC-Copilot off-topic vs on-topic responses | 1h |
| W2-D5 | Context Precision (1.11) | Evaluate retrieval ranking quality at k=4, 8 | 1h |
| W2-WE | Context Recall (1.12) + Context Relevancy (1.13) | Full RAGAS suite run on 10 DC-Copilot examples | 2.5h |

**Checkpoint:** Can explain each metric, run RAGAS programmatically, interpret scores.

### Weeks 3-4 — Advanced Eval, Production & Custom Metrics

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W3-D1 | Answer Correctness (1.14) | Build 20-row eval dataset with ground truth | 1h |
| W3-D2 | Answer Similarity (1.15) | Expand dataset to 50 rows, test similarity metric | 1h |
| W3-D3 | Human Eval (1.16) | Read frameworks (Likert, A/B, rubric-based) | 1h |
| W3-D4 | LLM-as-a-Judge (1.17) | Implement GPT-4 judge scoring rubric | 1.5h |
| W3-D5 | Custom Metrics (1.18) | Build part-number-validation metric for DC-Copilot | 1h |
| W3-WE | Comparison Table (1.19) + Eval Pipeline (1.20) | Write full eval script in a notebook | 2.5h |
| W4-D1 | Precision@K, Recall@K, MAP (1.21) | Add IR metrics to eval pipeline | 1h |
| W4-D2 | G-Eval (1.22) | Implement chain-of-thought evaluation | 1h |
| W4-D3 | SelfCheckGPT & Semantic Entropy (1.23) | Test reference-free hallucination detection | 1h |
| W4-D4 | Toxicity & Safety (1.24) + Observability (1.25) | Read + note what applies to DC-Copilot | 1h |
| W4-D5 | Drift Detection (1.26) | Understand regression monitoring patterns | 1h |
| W4-WE | Eval Tools (1.27) + LangSmith setup | Set up LangSmith tracing for DC-Copilot | 2.5h |

**Checkpoint:** End-to-end eval pipeline running, can discuss all metrics in an interview.

---

## Phase 2: Advanced RAG Algorithms (Weeks 5-8, ~32h)

### Weeks 5-6 — Core RAG Patterns

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W5-D1 | RAG Recap (2.1) | Map DC-Copilot's current architecture | 1h |
| W5-D2 | Naive vs Advanced (2.2) | Identify DC-Copilot's failure modes from the 7 listed | 1h |
| W5-D3 | Sentence Window (2.3) — theory | Read algorithm, understand window sizing | 1h |
| W5-D4 | Sentence Window (2.3) — code | Prototype with LlamaIndex on sample docs | 1.5h |
| W5-D5 | Parent-Child (2.4) — theory | Understand hierarchical chunking | 1h |
| W5-WE | Parent-Child (2.4) — code | Build page→paragraph→sentence hierarchy, test | 2.5h |
| W6-D1 | Hybrid Search (2.5) — theory | Understand vector + BM25 fusion | 1h |
| W6-D2 | Hybrid Search (2.5) — code | Write OpenSearch hybrid query for DC-Copilot | 1.5h |
| W6-D3 | HyDE (2.6) | Read + implement hypothetical doc generation | 1.5h |
| W6-D4 | Self-Query / Metadata Filtering (2.7) | Build metadata-aware retrieval | 1.5h |
| W6-D5 | Review W5-6 | Re-run eval pipeline on each variant, compare scores | 1h |
| W6-WE | Hands-on comparison | Benchmark Sentence Window vs Parent-Child vs Hybrid | 2.5h |

### Weeks 7-8 — Advanced & Agentic RAG

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W7-D1 | Corrective RAG (2.8) — theory | Understand relevance grading + fallback | 1h |
| W7-D2 | Corrective RAG (2.8) — code | Implement in LangGraph with grading node | 1.5h |
| W7-D3 | Adaptive RAG (2.9) | Map DC-Copilot's intent routing as adaptive RAG | 1h |
| W7-D4 | Graph RAG (2.10) — theory | Understand knowledge graphs + multi-hop reasoning | 1h |
| W7-D5 | Graph RAG (2.10) — code | Build small asset→component→part graph | 1.5h |
| W7-WE | RAG Fusion / Multi-Query (2.11) | Add query variation generation, test recall boost | 2.5h |
| W8-D1 | Agentic RAG (2.12) | Review DC-Copilot as agentic RAG, note gaps | 1h |
| W8-D2 | PageIndex / Vectorless RAG (2.13) | Evaluate for DC-Copilot manual lookups | 1h |
| W8-D3 | Comparison Matrix (2.14) | Fill out comparison table from your experiments | 1h |
| W8-D4 | DC-Copilot improvement plan | Write "top 3 RAG upgrades" recommendation doc | 1h |
| W8-D5 | Review | Revisit weakest algorithm, re-read + re-code | 1h |
| W8-WE | Final benchmarks | Run eval pipeline across all variants, document results | 2.5h |

**Checkpoint:** 4+ RAG algorithms prototyped and benchmarked, clear DC-Copilot upgrade path.

---

## Phase 3: Re-Ranking Methods (Weeks 9-10, ~15h)

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W9-D1 | Why Re-Ranking (3.1), Two-Stage Paradigm (3.2) | Read theory, understand bi-encoder vs cross-encoder | 1h |
| W9-D2 | Cross-Encoder (3.3) — theory | Understand scoring mechanism | 1h |
| W9-D3 | Cross-Encoder (3.3) — code | Implement `ms-marco-MiniLM` re-ranker | 1.5h |
| W9-D4 | Cohere Rerank (3.4) | Test Cohere API on DC-Copilot queries | 1h |
| W9-D5 | ColBERT (3.5) | Read late-interaction approach, compare | 1h |
| W9-WE | Cross-Encoder vs Cohere vs ColBERT | Benchmark all 3 on same query set | 2.5h |
| W10-D1 | LLM-Based Re-Ranking (3.6) | Implement pointwise LLM scoring | 1h |
| W10-D2 | RRF (3.7) | Implement Reciprocal Rank Fusion | 1h |
| W10-D3 | Custom Scoring (3.8) + FlashRank (3.9) | Enhance DC-Copilot's `SimpleMetrics`, test FlashRank | 1.5h |
| W10-D4 | Lost-in-the-Middle (3.10) + Comparison (3.11) | Implement position reordering, fill comparison matrix | 1h |
| W10-D5 | Best Practices (3.12) | Finalize re-ranking strategy for DC-Copilot | 1h |

**Checkpoint:** Re-ranking integrated, latency/quality tradeoffs documented.

---

## Phase 4: DBT on AWS (Weeks 11-12, ~12h)

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W11-D1 | What is DBT (4.1) | Read, install `dbt-core` + `dbt-snowflake` | 1h |
| W11-D2 | DBT on AWS (4.2) | Set up project with `profiles.yml` for DC-Copilot Snowflake | 1h |
| W11-D3 | Models + Sources (4.3) | Write staging models for work_orders, assets tables | 1.5h |
| W11-D4 | Seeds + Snapshots (4.3) | Create seed file for priority levels, write a snapshot | 1h |
| W11-D5 | Tests + Macros (4.3) | Add unique/not_null tests, write a custom macro | 1h |
| W11-WE | Materializations (4.3) | Practice table vs view vs incremental, understand tradeoffs | 2h |
| W12-D1 | DBT + Snowflake (4.4) | Build marts layer: work order metrics, asset health | 1.5h |
| W12-D2 | DBT + Redshift (4.5) | Read Redshift-specific patterns (sort keys, dist keys) | 1h |
| W12-D3 | Do's/Don'ts (4.6) + `dbt docs generate` | Run full pipeline, review docs site | 1h |

**Checkpoint:** dbt project running, `dbt test` + `dbt run` passing.

---

## Phase 5: Terraform (Weeks 13-16, ~28h)

### Weeks 13-14 — Terraform Fundamentals

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W13-D1 | IaC concepts | Read: Terraform vs CloudFormation vs Pulumi | 1h |
| W13-D2 | Install + first apply | `terraform init/plan/apply` a basic S3 bucket | 1h |
| W13-D3 | HCL syntax, providers | Write TF for DC-Copilot's S3 buckets | 1h |
| W13-D4 | Resources + data sources | Add DynamoDB table + SQS queue | 1h |
| W13-D5 | Variables + outputs | Parameterize with `variables.tf` and `terraform.tfvars` | 1h |
| W13-WE | Locals + tfvars per env | Set up sandbox/dev/prod variable files | 2h |
| W14-D1 | State management — local | Understand state file structure | 1h |
| W14-D2 | State management — remote | S3 backend + DynamoDB lock table | 1.5h |
| W14-D3 | `terraform import` | Import an existing AWS resource into state | 1h |
| W14-D4 | Modules — theory | Understand inputs, outputs, composition | 1h |
| W14-D5 | Modules — code | Refactor into storage + compute + networking modules | 1.5h |
| W14-WE | Workspaces + lifecycle | Multi-env deployment, `prevent_destroy`, `ignore_changes` | 2h |

### Weeks 15-16 — Advanced Terraform + DC-Copilot Infra

| Session | Topic | What to Do | Time |
|---------|-------|------------|------|
| W15-D1 | IAM roles + policies | Write DC-Copilot ECS task role + execution role | 1.5h |
| W15-D2 | IAM — assume_role + least privilege | OpenSearch serverless access policy | 1h |
| W15-D3 | VPC + subnets | Terraform DC-Copilot's VPC (public + private subnets) | 1.5h |
| W15-D4 | Security groups + VPC endpoints | Lock down traffic for OpenSearch + Snowflake | 1h |
| W15-D5 | ECS/Fargate — task definition | Define DC-Copilot API container | 1h |
| W15-WE | ECS/Fargate — service + ALB | Deploy behind load balancer with health checks | 2.5h |
| W16-D1 | Secrets Manager + Parameter Store | Terraform all DC-Copilot secrets | 1h |
| W16-D2 | CI/CD — `terraform plan` in GH Actions | Add plan step to PR workflow | 1.5h |
| W16-D3 | CI/CD — `terraform apply` on merge | Add apply step on main branch merge | 1h |
| W16-D4 | tflint + checkov | Run security scanning on DC-Copilot infra | 1h |
| W16-D5 | Full review | `terraform plan` entire DC-Copilot stack, verify clean | 1h |
| W16-WE | Polish | Fix warnings, add missing tags, clean up | 2h |

**Checkpoint:** DC-Copilot infra fully in Terraform, deployable via CI/CD.

---

## Phase 6: Integration & Mock Interviews (Weeks 17-18, ~15h)

| Session | Focus | What to Do | Time |
|---------|-------|------------|------|
| W17-D1 | System Design prep | Draw a production RAG system: eval + retrieval + infra | 1.5h |
| W17-D2 | Coding from memory | Implement eval pipeline from scratch (no reference) | 1.5h |
| W17-D3 | Coding from memory | Write a Terraform module from scratch (no reference) | 1.5h |
| W17-D4 | Verbal explanations | Practice explaining RAGAS, re-ranking, DBT materializations out loud | 1h |
| W17-D5 | DC-Copilot case study | Prepare 15-min "How I'd improve DC-Copilot's RAG" pitch | 1.5h |
| W17-WE | Mock interview #1 | System design: "Design a RAG eval platform" | 2h |
| W18-D1 | Review weak spots | Revisit lowest-confidence topics | 1h |
| W18-D2 | Cheat sheet | Finalize 1-page-per-topic summary cards | 1h |
| W18-D3 | Mock interview #2 | "Walk me through deploying an ML system with Terraform" | 1.5h |
| W18-D4 | Mock interview #3 | "How do you evaluate and monitor RAG in production?" | 1.5h |
| W18-D5 | Final confidence check | Go through 44-topic checklist, flag any remaining gaps | 1h |

**Checkpoint:** Can whiteboard and discuss all topics confidently at senior level.

---

## Quick Reference: Topic Inventory (44 topics)

### LLM/RAG Evaluation (27 topics)
- [ ] Evaluation Taxonomy (3 layers)
- [ ] BLEU Score
- [ ] ROUGE (ROUGE-1, ROUGE-2, ROUGE-L)
- [ ] METEOR
- [ ] BERTScore
- [ ] Perplexity
- [ ] RAGAS Framework (install + run)
- [ ] Faithfulness / Groundedness
- [ ] Answer Relevancy
- [ ] Context Precision
- [ ] Context Recall
- [ ] Context Relevancy
- [ ] Answer Correctness
- [ ] Answer Semantic Similarity
- [ ] MRR and NDCG
- [ ] Human Evaluation Frameworks
- [ ] LLM-as-a-Judge
- [ ] Custom Domain Metrics
- [ ] Building an Eval Pipeline
- [ ] Precision@K, Recall@K, Hit Rate, MAP
- [ ] G-Eval
- [ ] SelfCheckGPT & Semantic Entropy
- [ ] Toxicity & Safety Scoring
- [ ] Production Observability Metrics
- [ ] Drift Detection & Regression Monitoring
- [ ] Eval Tools (LangSmith, DeepEval, LangFuse)
- [ ] CI/CD Eval Integration

### Advanced RAG (13 topics)
- [ ] Naive vs Advanced RAG (failure modes)
- [ ] Sentence Window Retrieval
- [ ] Parent-Child (Hierarchical) Retrieval
- [ ] Hybrid Search (Vector + BM25 + RRF)
- [ ] HyDE (Hypothetical Document Embeddings)
- [ ] Self-Query / Metadata Filtering
- [ ] Corrective RAG (CRAG)
- [ ] Adaptive RAG
- [ ] Graph RAG
- [ ] RAG Fusion / Multi-Query RAG
- [ ] Agentic RAG
- [ ] PageIndex (Vectorless RAG)
- [ ] Algorithm Selection & Comparison

### Re-Ranking (10 topics)
- [ ] Two-Stage Retrieval Paradigm
- [ ] Cross-Encoder Re-Ranking
- [ ] Cohere Rerank API
- [ ] ColBERT Re-Ranking
- [ ] LLM-Based Re-Ranking
- [ ] Reciprocal Rank Fusion (RRF)
- [ ] Custom Scoring Functions
- [ ] FlashRank / Lightweight Re-Rankers
- [ ] Lost-in-the-Middle Reordering
- [ ] Re-Ranking Strategy Selection

### DBT (6 topics)
- [ ] DBT Core Concepts (models, sources, seeds, snapshots)
- [ ] Tests & Macros
- [ ] Materializations (table, view, incremental, ephemeral)
- [ ] DBT + Snowflake on AWS
- [ ] DBT + Redshift
- [ ] DBT Best Practices & CI/CD

### Terraform (10 topics)
- [ ] HCL Syntax & Core Workflow (init/plan/apply)
- [ ] Providers, Resources, Data Sources
- [ ] Variables, Outputs, Locals
- [ ] State Management (remote backend, locking)
- [ ] Modules (structure, registry, composition)
- [ ] Workspaces & Multi-Environment
- [ ] AWS Provider (IAM, VPC, ECS, Secrets)
- [ ] Import & Drift Detection
- [ ] CI/CD Integration (GitHub Actions)
- [ ] Security Scanning (tflint, checkov)

---

## Weekly Rhythm (template)

```
Monday-Friday:  1 hour/day after work (read + small code exercise)
Saturday:       1.5-2 hours (hands-on coding / prototyping)
Sunday:         1-1.5 hours (review + notes + cheat sheet update)
                ─────────────
                ~10 hours/week
```

## Study Tips

1. **1 topic = 1 session** — Don't cram 2 topics into one hour; depth beats breadth
2. **Code every other day** — Alternate: Day 1 read theory, Day 2 implement it
3. **DC-Copilot is your interview story** — Tie every topic back to a real example
4. **Weekend = hands-on** — Weekdays for reading, weekends for coding
5. **Keep a cheat sheet** — One page per topic: what, why, when, DC-Copilot example
6. **Don't skip Phase 6** — Mock interviews are where knowledge becomes confidence

---

*Generated: 2026-03-18 | Pace: ~10h/week | Estimated completion: ~18 weeks (~4.5 months)*
