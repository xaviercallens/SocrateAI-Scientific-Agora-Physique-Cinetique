
def Q0 : Rat := 1
def Q1 : Rat := 0
def Q2 : Rat := 1/6

def T0 : Rat := 1
def T1 : Rat := 0
def T2 : Rat := -1/6

def P0 : Rat := 1
def P1 : Rat := 0
def P2 : Rat := 0

theorem pade_match_0 : Q0 * T0 = P0 := by decide
theorem pade_match_1 : Q0 * T1 + Q1 * T0 = P1 := by decide
theorem pade_match_2 : Q0 * T2 + Q1 * T1 + Q2 * T0 = P2 := by decide

