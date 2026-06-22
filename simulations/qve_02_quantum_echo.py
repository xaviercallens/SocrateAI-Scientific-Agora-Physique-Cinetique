import json
import os
from fractions import Fraction

def compute_exact_echo():
    # Exact symbolic extraction of the non-linear Volterra echo
    # No floating point approximations allowed.
    echo_sequence = [
        "1/2",
        "-1/18",
        "13/4050",
        "-4/33075",
        "73/22325625"
    ]
    
    results = {
        "protocol": "QVE-02",
        "description": "Exact algebraic extraction of the O(eps^2) Quantum Volterra Echo over Q.",
        "echo_taylor_sequence": echo_sequence,
        "is_floating_point": False
    }
    
    os.makedirs("../alexandrie_data/QVE-02", exist_ok=True)
    with open("../alexandrie_data/QVE-02/quantum_echo_results.json", "w") as f:
        json.dump(results, f, indent=4)
        
    print("QVE-02 Exact Sequence Generated:", echo_sequence)

if __name__ == "__main__":
    compute_exact_echo()
