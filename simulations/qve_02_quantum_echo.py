import sys
from pathlib import Path

# Add the project root directory to sys.path to resolve imports correctly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agora_swarm.orchestrator import AgentSocrate

if __name__ == "__main__":
    socrate = AgentSocrate()
    socrate.execute_protocol()
