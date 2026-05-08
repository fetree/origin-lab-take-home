"""
Usage:
  python -m simulator.main --scenario happy_path
  python -m simulator.main --scenario rejected
  python -m simulator.main --scenario pipeline_failure
  python -m simulator.main --scenario all          # run all three sequentially

Options:
  --api-url   Backend URL (default: http://localhost:8000)
  --speed     Simulation speed multiplier (default: 10 = 10× faster than real-time)
"""

import argparse
import asyncio
import logging

from simulator.scenarios import happy_path, pipeline_failure, rejected

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SCENARIOS = {
    "happy_path": happy_path.run,
    "rejected": rejected.run,
    "pipeline_failure": pipeline_failure.run,
}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default="happy_path",
                        choices=[*SCENARIOS, "all"])
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--speed", type=float, default=10.0,
                        help="Simulation speed multiplier (10 = 10× faster than real-time)")
    args = parser.parse_args()

    if args.scenario == "all":
        for name, fn in SCENARIOS.items():
            print(f"\n{'='*50}\nRunning scenario: {name}\n{'='*50}")
            await fn(args.api_url, args.speed)
    else:
        await SCENARIOS[args.scenario](args.api_url, args.speed)


if __name__ == "__main__":
    asyncio.run(main())
