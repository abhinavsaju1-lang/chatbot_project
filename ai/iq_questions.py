import random

# Adaptive IQ Question Bank organized by Difficulty Level (Easy, Medium, Hard) and Categories
IQ_QUESTION_BANK = {
    'easy': [
        {
            'id': 'e1',
            'category': 'Number Sequence',
            'question': 'What is the next number in this sequence? 2, 4, 6, 8, ?',
            'options': ['9', '10', '11', '12'],
            'answer': '10',
            'explanation': 'Add 2 to each term (2+2=4, 4+2=6, 6+2=8, 8+2=10).'
        },
        {
            'id': 'e2',
            'category': 'Logical Analogy',
            'question': 'Dog is to Puppy as Cat is to:',
            'options': ['Kitten', 'Calf', 'Cub', 'Foal'],
            'answer': 'Kitten',
            'explanation': 'A kitten is a baby cat, just as a puppy is a baby dog.'
        },
        {
            'id': 'e3',
            'category': 'Pattern Recognition',
            'question': 'Which word does NOT belong with the others?',
            'options': ['Apple', 'Banana', 'Carrot', 'Orange'],
            'answer': 'Carrot',
            'explanation': 'Carrot is a vegetable, while the others are fruits.'
        },
        {
            'id': 'e4',
            'category': 'Number Sequence',
            'question': 'What comes next in the series? 5, 10, 15, 20, ?',
            'options': ['22', '24', '25', '30'],
            'answer': '25',
            'explanation': 'Add 5 to each preceding term.'
        },
        {
            'id': 'e5',
            'category': 'Visual/Text Reasoning',
            'question': 'If a clock shows 3:00 PM, what angle is formed between the hour and minute hands?',
            'options': ['45 degrees', '90 degrees', '120 degrees', '180 degrees'],
            'answer': '90 degrees',
            'explanation': 'At 3:00, the minute hand points to 12 and the hour hand to 3, forming a right angle (90 degrees).'
        },
        {
            'id': 'e6',
            'category': 'Memory',
            'question': 'Memorize this code: 7 - 3 - 9 - 1. Which digit was third in the sequence?',
            'options': ['7', '3', '9', '1'],
            'answer': '9',
            'explanation': 'The third digit in 7 - 3 - 9 - 1 is 9.'
        },
        {
            'id': 'e7',
            'category': 'Analytical Reasoning',
            'question': 'Which number is smaller than 0.5 but larger than 0.2?',
            'options': ['0.1', '0.35', '0.6', '0.15'],
            'answer': '0.35',
            'explanation': '0.35 lies strictly between 0.2 and 0.5.'
        },
        {
            'id': 'e8',
            'category': 'Alphabet Reasoning',
            'question': 'What is the next letter in the sequence: B, D, F, H, ?',
            'options': ['I', 'J', 'K', 'L'],
            'answer': 'J',
            'explanation': 'Skip one letter each time (+2): B(2), D(4), F(6), H(8), J(10).'
        },
        {
            'id': 'e9',
            'category': 'Logical Analogy',
            'question': 'Bird is to Fly as Fish is to:',
            'options': ['Water', 'Swim', 'Gill', 'Scale'],
            'answer': 'Swim',
            'explanation': 'A bird moves by flying; a fish moves by swimming.'
        },
        {
            'id': 'e10',
            'category': 'Spatial Deduction',
            'question': 'If you turn clockwise by 90 degrees twice, which direction are you facing relative to start?',
            'options': ['Same direction', 'Opposite direction', 'Left', 'Right'],
            'answer': 'Opposite direction',
            'explanation': '90 + 90 = 180 degrees, which is directly opposite the starting direction.'
        }
    ],

    'medium': [
        {
            'id': 'm1',
            'category': 'Number Sequence',
            'question': 'What is the next number in this sequence? 3, 6, 12, 24, ?',
            'options': ['30', '36', '42', '48'],
            'answer': '48',
            'explanation': 'Each number is multiplied by 2 (24 * 2 = 48).'
        },
        {
            'id': 'm2',
            'category': 'Logical Deduction',
            'question': 'All roses are flowers. Some flowers fade quickly. Therefore:',
            'options': ['All roses fade quickly', 'Some roses fade quickly', 'Cannot be determined with certainty', 'No roses fade quickly'],
            'answer': 'Cannot be determined with certainty',
            'explanation': 'The premise states SOME flowers fade, which may or may not include roses.'
        },
        {
            'id': 'm3',
            'category': 'Pattern Recognition',
            'question': 'Complete the series: J, F, M, A, M, J, J, A, S, ?',
            'options': ['O', 'N', 'D', 'P'],
            'answer': 'O',
            'explanation': 'These are the first letters of the months of the year (January, February... September, October).'
        },
        {
            'id': 'm4',
            'category': 'Analytical Reasoning',
            'question': 'If 3 cats can catch 3 mice in 3 minutes, how many cats are needed to catch 100 mice in 100 minutes?',
            'options': ['3', '100', '33', '1'],
            'answer': '3',
            'explanation': 'Each cat catches 1 mouse per 3 minutes. Thus 3 cats catch 100 mice in 100 minutes.'
        },
        {
            'id': 'm5',
            'category': 'Number Sequence',
            'question': 'What comes next? 1, 4, 9, 16, 25, ?',
            'options': ['30', '32', '35', '36'],
            'answer': '36',
            'explanation': 'These are perfect squares: 1^2, 2^2, 3^2, 4^2, 5^2, 6^2 = 36.'
        },
        {
            'id': 'm6',
            'category': 'Visual/Text Reasoning',
            'question': 'A man drives 4 miles North, then turns East and drives 3 miles. How far is he from his starting point?',
            'options': ['5 miles', '7 miles', '4 miles', '6 miles'],
            'answer': '5 miles',
            'explanation': 'Using the Pythagorean theorem: sqrt(4^2 + 3^2) = sqrt(16 + 9) = sqrt(25) = 5 miles.'
        },
        {
            'id': 'm7',
            'category': 'Memory',
            'question': 'Recall: RED, BLUE, GREEN, YELLOW. If reversed, which color comes second?',
            'options': ['RED', 'BLUE', 'GREEN', 'YELLOW'],
            'answer': 'GREEN',
            'explanation': 'Reversed order: YELLOW, GREEN, BLUE, RED. Second color is GREEN.'
        },
        {
            'id': 'm8',
            'category': 'Alphabet Logic',
            'question': 'If CAT is coded as 3-1-20, what is DOG coded as?',
            'options': ['4-15-7', '4-14-7', '3-15-8', '5-15-7'],
            'answer': '4-15-7',
            'explanation': 'Letters mapped to alphabetical positions: D=4, O=15, G=7.'
        },
        {
            'id': 'm9',
            'category': 'Numerical Reasoning',
            'question': 'Find the missing number in the sequence: 7, 14, 28, 56, ?',
            'options': ['112', '108', '84', '124'],
            'answer': '112',
            'explanation': 'Each term is doubled: 56 * 2 = 112.'
        },
        {
            'id': 'm10',
            'category': 'Logical Deduction',
            'question': 'No rectangles are circles. All squares are rectangles. Therefore:',
            'options': ['All squares are circles', 'No squares are circles', 'Some squares are circles', 'Cannot be determined'],
            'answer': 'No squares are circles',
            'explanation': 'Since all squares belong to the rectangle category and no rectangles are circles, no squares can be circles.'
        }
    ],

    'hard': [
        {
            'id': 'h1',
            'category': 'Number Sequence',
            'question': 'What is the next number in the Fibonacci sequence? 2, 3, 5, 8, 13, 21, ?',
            'options': ['28', '34', '39', '42'],
            'answer': '34',
            'explanation': 'Each number is the sum of the preceding two (13 + 21 = 34).'
        },
        {
            'id': 'h2',
            'category': 'Logical Deduction',
            'question': 'If Tom is taller than Dick, and Dick is shorter than Harry, which statement must be true?',
            'options': ['Tom is taller than Harry', 'Harry is taller than Tom', 'Dick is the shortest of the three', 'Tom and Harry are equal height'],
            'answer': 'Dick is the shortest of the three',
            'explanation': 'Both Tom and Harry are taller than Dick, so Dick is definitely the shortest.'
        },
        {
            'id': 'h3',
            'category': 'Analytical Reasoning',
            'question': 'A lily pad doubles in size every day. If it takes 48 days to cover a lake, on which day was the lake half-covered?',
            'options': ['24', '47', '46', '12'],
            'answer': '47',
            'explanation': 'Since it doubles every day, on day 47 it was half the size of day 48.'
        },
        {
            'id': 'h4',
            'category': 'Pattern Recognition',
            'question': 'What is the missing term? 2, 6, 12, 20, 30, ?',
            'options': ['38', '40', '42', '44'],
            'answer': '42',
            'explanation': 'Differences increase by 2: +4, +6, +8, +10, +12 -> 30 + 12 = 42 (also n*(n+1)).'
        },
        {
            'id': 'h5',
            'category': 'Visual/Text Reasoning',
            'question': 'How many triangles are formed by drawing both diagonals inside a square?',
            'options': ['4', '6', '8', '10'],
            'answer': '8',
            'explanation': '4 small single triangles + 4 large combined triangles = 8 total triangles.'
        },
        {
            'id': 'h6',
            'category': 'Memory & Spatial',
            'question': 'Imagine a cube painted red on all 6 faces, then cut into 27 equal smaller cubes. How many small cubes have red paint on EXACTLY 2 faces?',
            'options': ['6', '8', '12', '18'],
            'answer': '12',
            'explanation': 'Cubes with 2 faces painted are along the 12 edges (excluding corners).'
        },
        {
            'id': 'h7',
            'category': 'Abstract Math Logic',
            'question': 'In a tournament of 64 players with single elimination, how many total matches must be played to determine the champion?',
            'options': ['64', '63', '32', '127'],
            'answer': '63',
            'explanation': 'Each match eliminates exactly 1 player. To eliminate 63 players out of 64 requires exactly 63 matches.'
        },
        {
            'id': 'h8',
            'category': 'Number Series Deduction',
            'question': 'What comes next in the sequence? 3, 5, 9, 17, 33, ?',
            'options': ['49', '57', '65', '67'],
            'answer': '65',
            'explanation': 'Differences are powers of 2: +2, +4, +8, +16, +32 -> 33 + 32 = 65 (also 2*n - 1).'
        },
        {
            'id': 'h9',
            'category': 'Spatial Logic',
            'question': 'If a clock loses 4 minutes every hour, and is set correctly at 12:00 noon, what time will it show at 6:00 PM?',
            'options': ['5:24 PM', '5:36 PM', '5:40 PM', '5:44 PM'],
            'answer': '5:36 PM',
            'explanation': 'Over 6 hours, it loses 6 * 4 = 24 minutes. 6:00 PM minus 24 minutes is 5:36 PM.'
        },
        {
            'id': 'h10',
            'category': 'Deductive Syllogism',
            'question': 'All pilots are trained. Some astronauts are pilots. No untrained person is a scientist. Therefore:',
            'options': ['All astronauts are scientists', 'Some astronauts are trained', 'No pilots are scientists', 'All scientists are pilots'],
            'answer': 'Some astronauts are trained',
            'explanation': 'Since all pilots are trained and some astronauts are pilots, those astronauts are definitely trained.'
        }
    ]
}

def get_fallback_iq_batch():
    """
    Returns a guaranteed, high-quality, randomized 20-question psychometric test
    structured as: 7 Easy, 7 Medium, 6 Hard.
    Used when external LLM APIs hit rate limits or capacity bottlenecks.
    """
    easy_pool = list(IQ_QUESTION_BANK['easy'])
    medium_pool = list(IQ_QUESTION_BANK['medium'])
    hard_pool = list(IQ_QUESTION_BANK['hard'])

    random.shuffle(easy_pool)
    random.shuffle(medium_pool)
    random.shuffle(hard_pool)

    selected = easy_pool[:7] + medium_pool[:7] + hard_pool[:6]

    formatted_batch = []
    for idx, q in enumerate(selected):
        difficulty = 'easy' if idx < 7 else ('medium' if idx < 14 else 'hard')
        formatted_batch.append({
            'id': f"fallback_{difficulty}_{random.randint(10000, 99999)}",
            'difficulty': difficulty,
            'category': q.get('category', 'Logical Reasoning'),
            'question': q.get('question', ''),
            'options': q.get('options', ['A', 'B', 'C', 'D']),
            'answer': q.get('answer', ''),
            'explanation': q.get('explanation', '')
        })

    return formatted_batch

def get_adaptive_question(difficulty='easy', asked_ids=None):
    """
    Select a random, non-repeated question for the specified difficulty level (easy, medium, hard).
    """
    asked_ids = asked_ids or []
    candidates = [q for q in IQ_QUESTION_BANK.get(difficulty, IQ_QUESTION_BANK['easy']) if q['id'] not in asked_ids]

    if not candidates:
        # Fallback to any unasked question across all pools
        all_qs = IQ_QUESTION_BANK['easy'] + IQ_QUESTION_BANK['medium'] + IQ_QUESTION_BANK['hard']
        candidates = [q for q in all_qs if q['id'] not in asked_ids]

    if not candidates:
        # If all questions asked, pick a random one
        candidates = IQ_QUESTION_BANK.get(difficulty, IQ_QUESTION_BANK['easy'])

    return random.choice(candidates)
