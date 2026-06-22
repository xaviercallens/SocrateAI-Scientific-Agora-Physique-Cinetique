
def Q0 : Int := 6
def Q1 : Int := 0
def Q2 : Int := 1

def T0 : Int := 6
def T1 : Int := 0
def T2 : Int := -1

def P0 : Int := 36
def P1 : Int := 0
def P2 : Int := 0

theorem pade_match_0 : Q0 * T0 = P0 := by rfl
theorem pade_match_1 : Q0 * T1 + Q1 * T0 = P1 := by rfl
theorem pade_match_2 : Q0 * T2 + Q1 * T1 + Q2 * T0 = P2 := by rfl

