"""Run fixed evaluation tasks.

Default mode is dry documentation only for --help.
Use --real to call DeepSeek (requires .env, costs quota).

Examples:
  python scripts/run_evaluation.py --real --limit 5
  python scripts/run_evaluation.py --real --category safety
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mini_agent.config import load_settings
from mini_agent.evaluation.loader import load_tasks
from mini_agent.evaluation.models import TaskCategory
from mini_agent.evaluation.report import write_report_json, write_report_markdown
from mini_agent.evaluation.runner import EvaluationRunner
from mini_agent.llm.deepseek_client import DeepSeekClient

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_PATH = REPO_ROOT / "evals" / "tasks" / "repository_tasks.json"
FIXTURES_DIR = REPO_ROOT / "evals" / "fixtures"
OUT_DIR = REPO_ROOT / "evals" / "results" / "real"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Mini Agent evaluation tasks")
    parser.add_argument(
        "--real",
        action="store_true",
        help="Use DeepSeek (required for this script)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Max tasks to run")
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        choices=[item.value for item in TaskCategory],
        help="Filter by category",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=OUT_DIR,
        help="Directory for report.json / report.md",
    )
    args = parser.parse_args()

    if not args.real:
        raise SystemExit(
            "This script requires --real (DeepSeek).\n"
            "For a no-API demo, run: python scripts/run_evaluation_demo.py"
        )

    settings = load_settings()
    tasks = load_tasks(TASKS_PATH, fixtures_dir=FIXTURES_DIR, require_minimum=True)
    category = TaskCategory(args.category) if args.category else None

    client = DeepSeekClient.from_settings(settings=settings)
    try:
        runner = EvaluationRunner(llm=client, fixtures_dir=FIXTURES_DIR)
        report = runner.run(tasks, limit=args.limit, category=category)
    finally:
        client.close()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.out_dir / "report.json"
    md_path = args.out_dir / "report.md"
    write_report_json(report, json_path)
    write_report_markdown(report, md_path)

    print(f"total={report.total_tasks}")
    print(f"passed={report.passed_count} failed={report.failed_count}")
    print(f"success_rate={report.success_rate:.1%}")
    print(f"failed_task_ids={report.failed_task_ids}")
    print(f"wrote {json_path}")
    print(f"wrote {md_path}")


if __name__ == "__main__":
    main()
