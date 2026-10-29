# Evaluation summary (automatic scores)

## multi_qwen3-8b

Runs: 3; question-runs: 90

| Category | Accuracy | Groundedness (correct citation) | Wrongly refused / wrongly answered |
|---|---|---|---|
| email | 87% (13/15) | 17% (2/12) | 2 refused / 0 answered |
| out_of_scope | 78% (14/18) | n/a | 0 refused / 4 answered |
| policy | 77% (30/39) | 82% (32/39) | 5 refused / 0 answered |
| schedule | 94% (17/18) | 94% (17/18) | 1 refused / 0 answered |
| ALL | 82% (74/90) | 74% (51/69) | 8 refused / 4 answered |

Failed model calls (timeouts): 0

Questions whose correctness or tool path changed across runs: 16 of 30

| Q | Question | Correct per run | Distinct tool paths |
|---|---|---|---|
| 1 | What is the attendance requirement to sit in the Major exam? | Y N N | 2 |
| 6 | What happens if a student is absent from all academic activities for f | Y N Y | 2 |
| 7 | Within how many days must I apply for a make-up examination after miss | Y Y N | 2 |
| 8 | For how many days can a student be granted short leave on medical grou | Y Y N | 2 |
| 10 | How many extra credits can a student take from the sixth semester onwa | Y Y N | 1 |
| 11 | What are the grade points for a B grade? | Y N N | 2 |
| 13 | Who can recommend de-registration of a student whose attendance falls  | N Y Y | 2 |
| 15 | What is the slot of the course Artificial Intelligence (CSL3090)? | Y Y Y | 2 |
| 19 | What is the slot of the course Fundamentals of Logic (HSL4010)? | Y N Y | 1 |
| 20 | Write an email to the course instructor of ENL7010 that I need leave f | Y Y N | 2 |
| 23 | What is the email id of the instructor of HSL4010? | N Y Y | 2 |
| 26 | What is the best way to reach the campus from Jodhpur city center? | N N Y | 1 |
| 27 | Who won the last cricket world cup? | Y Y N | 1 |
| 28 | What is the hostel fee for B.Tech. students? | Y Y Y | 3 |
| 29 | What will the weather in Jodhpur be like tomorrow? | N Y Y | 1 |
| 30 | Write a Python function to reverse a string. | Y Y Y | 2 |

Questions with word-for-word identical answers in every run: 3 of 30

Questions answered incorrectly in at least one run:

- Q1 (2/3 runs wrong): What is the attendance requirement to sit in the Major exam?
- Q6 (1/3 runs wrong): What happens if a student is absent from all academic activities for four or mor
- Q7 (1/3 runs wrong): Within how many days must I apply for a make-up examination after missing an exa
- Q8 (1/3 runs wrong): For how many days can a student be granted short leave on medical grounds?
- Q10 (1/3 runs wrong): How many extra credits can a student take from the sixth semester onwards?
- Q11 (2/3 runs wrong): What are the grade points for a B grade?
- Q13 (1/3 runs wrong): Who can recommend de-registration of a student whose attendance falls below 75% 
- Q19 (1/3 runs wrong): What is the slot of the course Fundamentals of Logic (HSL4010)?
- Q20 (1/3 runs wrong): Write an email to the course instructor of ENL7010 that I need leave for 2 days 
- Q23 (1/3 runs wrong): What is the email id of the instructor of HSL4010?
- Q26 (2/3 runs wrong): What is the best way to reach the campus from Jodhpur city center?
- Q27 (1/3 runs wrong): Who won the last cricket world cup?
- Q29 (1/3 runs wrong): What will the weather in Jodhpur be like tomorrow?

## single_qwen3-8b

Runs: 2; question-runs: 60

| Category | Accuracy | Groundedness (correct citation) | Wrongly refused / wrongly answered |
|---|---|---|---|
| email | 100% (10/10) | 38% (3/8) | 0 refused / 0 answered |
| out_of_scope | 92% (11/12) | n/a | 0 refused / 1 answered |
| policy | 77% (20/26) | 85% (22/26) | 2 refused / 0 answered |
| schedule | 83% (10/12) | 92% (11/12) | 1 refused / 0 answered |
| ALL | 85% (51/60) | 78% (36/46) | 3 refused / 1 answered |

Failed model calls (timeouts): 2

Questions whose correctness or tool path changed across runs: 10 of 30

| Q | Question | Correct per run | Distinct tool paths |
|---|---|---|---|
| 4 | How long is the Major examination? | Y N | 2 |
| 10 | How many extra credits can a student take from the sixth semester onwa | N N | 2 |
| 12 | How long is the Minor examination? | N Y | 2 |
| 15 | What is the slot of the course Artificial Intelligence (CSL3090)? | Y N | 2 |
| 19 | What is the slot of the course Fundamentals of Logic (HSL4010)? | N Y | 2 |
| 22 | I was sick for 3 days. Write a sick leave email to the instructor of L | Y Y | 2 |
| 24 | Write an email to the course instructor of CSL7650 that I need leave f | Y Y | 2 |
| 25 | What are the available dining options on the campus? | Y Y | 2 |
| 26 | What is the best way to reach the campus from Jodhpur city center? | N Y | 2 |
| 28 | What is the hostel fee for B.Tech. students? | Y Y | 2 |

Questions with word-for-word identical answers in every run: 7 of 30

Questions answered incorrectly in at least one run:

- Q1 (2/2 runs wrong): What is the attendance requirement to sit in the Major exam?
- Q4 (1/2 runs wrong): How long is the Major examination?
- Q10 (2/2 runs wrong): How many extra credits can a student take from the sixth semester onwards?
- Q12 (1/2 runs wrong): How long is the Minor examination?
- Q15 (1/2 runs wrong): What is the slot of the course Artificial Intelligence (CSL3090)?
- Q19 (1/2 runs wrong): What is the slot of the course Fundamentals of Logic (HSL4010)?
- Q26 (1/2 runs wrong): What is the best way to reach the campus from Jodhpur city center?
