# Turso Run 13 vs Run 12 - Detailed Comparison

## Overall Results

**Run 13 (Phase 2 with enhanced embeddings)**: 84.0% execution match
**Run 12 (Phase 1)**: 84.0% execution match
**Net Change**: 0.0% (but individual databases changed significantly)

## Database-Level Changes

### Biggest Improvements
1. **museum_visit**: 94.4% vs 72.2% = **+22.2%** (+4 questions)
2. **battle_death**: 81.3% vs 68.8% = **+12.5%** (+2 questions)
3. **cre_Doc_Template_Mgt**: 84.5% vs 78.6% = **+5.9%** (+5 questions)
4. **course_teach**: 86.7% vs 83.3% = **+3.4%** (+1 question)
5. **employee_hire_evaluation**: 94.7% vs 92.1% = **+2.6%** (+1 question)

### Biggest Degradations
1. **network_1**: 82.1% vs 87.5% = **-5.4%** (-3 questions)
2. **student_transcripts_tracking**: 74.4% vs 79.5% = **-5.1%** (-4 questions)
3. **flight_2**: 88.8% vs 92.5% = **-3.7%** (-3 questions)
4. **singer**: 90.0% vs 93.3% = **-3.3%** (-1 question)
5. **orchestra**: 95.0% vs 97.5% = **-2.5%** (-1 question)
6. **world_1**: 74.2% vs 75.8% = **-1.6%** (-2 questions)

### Unchanged
- concert_singer: 86.7%
- pets_1: 100.0%
- poker_player: 100.0%
- real_estate_properties: 75.0%
- voter_1: 93.3%
- wta_1: 32.3%

## Complete Database Results

| Database | Run 13 | Run 12 | Change | Questions Changed |
|----------|--------|--------|--------|-------------------|
| battle_death | 81.3% | 68.8% | **+12.5%** | +2 |
| car_1 | 69.6% | 67.4% | +2.2% | +2 |
| concert_singer | 86.7% | 86.7% | 0.0% | 0 |
| course_teach | 86.7% | 83.3% | +3.4% | +1 |
| cre_Doc_Template_Mgt | 84.5% | 78.6% | +5.9% | +5 |
| dog_kennels | 81.7% | 79.3% | +2.4% | +2 |
| employee_hire_evaluation | 94.7% | 92.1% | +2.6% | +1 |
| flight_2 | 88.8% | 92.5% | **-3.7%** | -3 |
| museum_visit | 94.4% | 72.2% | **+22.2%** | +4 |
| network_1 | 82.1% | 87.5% | **-5.4%** | -3 |
| orchestra | 95.0% | 97.5% | -2.5% | -1 |
| pets_1 | 100.0% | 100.0% | 0.0% | 0 |
| poker_player | 100.0% | 100.0% | 0.0% | 0 |
| real_estate_properties | 75.0% | 75.0% | 0.0% | 0 |
| singer | 90.0% | 93.3% | **-3.3%** | -1 |
| student_transcripts_tracking | 74.4% | 79.5% | **-5.1%** | -4 |
| tvshow | 85.5% | 83.9% | +1.6% | +1 |
| voter_1 | 93.3% | 93.3% | 0.0% | 0 |
| world_1 | 74.2% | 75.8% | -1.6% | -2 |
| wta_1 | 32.3% | 32.3% | 0.0% | 0 |

## Analysis Priority

1. Investigate **degraded databases** (6 databases, -14 questions total):
   - network_1, student_transcripts_tracking, flight_2 (biggest losses)
   - singer, orchestra, world_1

2. Learn from **improved databases** (9 databases, +18 questions total):
   - museum_visit, battle_death, cre_Doc_Template_Mgt (biggest wins)
   - What Phase 2 features helped?

3. Net improvement: +4 questions overall (18 improved - 14 degraded)
