// MindSense 1-by-1 Adaptive IQ Test Engine with 1s Visual Option Feedback

let activeSessionId = null;
let currentQuestionTimeLeft = 30;
let timerInterval = null;
let selectedOptionValue = null;
let currentQuestionStartTime = Date.now();

async function startIQTestSession() {
    const btn = document.getElementById('btn-start');
    const text = document.getElementById('start-text');
    const spinner = document.getElementById('start-spinner');
    
    btn.disabled = true;
    text.textContent = "Generating Unique Test...";
    spinner.classList.remove('hidden');

    try {
        const response = await fetch('/api/iq/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();
        if (data.success) {
            document.getElementById('start-screen').classList.add('hidden');
            document.getElementById('quiz-screen').classList.remove('hidden');
            activeSessionId = data.session_id;
            renderQuestion(data);
        } else {
            alert(data.error || 'Failed to start test.');
            btn.disabled = false;
            text.textContent = "Begin Assessment Now";
            spinner.classList.add('hidden');
        }
    } catch (err) {
        alert('Network error starting test.');
        btn.disabled = false;
        text.textContent = "Begin Assessment Now";
        spinner.classList.add('hidden');
    }
}

function renderQuestion(data) {
    selectedOptionValue = null;
    currentQuestionStartTime = Date.now();
    
    document.getElementById('question-progress').textContent = `Question ${data.question_index} / ${data.total_questions}`;
    document.getElementById('difficulty-badge').textContent = data.difficulty;
    document.getElementById('category-badge').textContent = data.category;
    document.getElementById('question-text').textContent = data.question;

    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';

    data.options.forEach((opt, idx) => {
        const btn = document.createElement('button');
        btn.setAttribute('data-option-val', opt);
        btn.className = 'iq-option-btn p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-left font-semibold text-slate-800 dark:text-slate-100 hover:border-blue-500 transition flex items-center gap-3 w-full';
        btn.onclick = () => selectOption(btn, opt);

        btn.innerHTML = `
            <span class="w-7 h-7 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-bold flex items-center justify-center shrink-0">
                ${String.fromCharCode(65 + idx)}
            </span>
            <span>${escapeHtml(opt)}</span>
        `;
        optionsContainer.appendChild(btn);
    });

    document.getElementById('btn-next-q').disabled = true;
    startQuestionTimer();
}

function selectOption(btnElement, value) {
    const allBtns = document.querySelectorAll('.iq-option-btn');
    allBtns.forEach(b => {
        b.classList.remove('border-blue-500', 'bg-blue-500/10', 'text-blue-600', 'dark:text-blue-400');
    });

    // Highlight Selected Option BLUE
    btnElement.classList.add('border-blue-500', 'bg-blue-500/10', 'text-blue-600', 'dark:text-blue-400');
    selectedOptionValue = value;
    document.getElementById('btn-next-q').disabled = false;
}

function startQuestionTimer() {
    clearInterval(timerInterval);
    currentQuestionTimeLeft = 30;
    const timerDisplay = document.getElementById('timer-display');
    timerDisplay.textContent = `${currentQuestionTimeLeft}s`;

    timerInterval = setInterval(() => {
        currentQuestionTimeLeft--;
        timerDisplay.textContent = `${currentQuestionTimeLeft}s`;

        if (currentQuestionTimeLeft <= 0) {
            clearInterval(timerInterval);
            submitSelectedAnswer(true);
        }
    }, 1000);
}

async function submitSelectedAnswer(isTimeout = false) {
    clearInterval(timerInterval);
    const timeTaken = Math.round((Date.now() - currentQuestionStartTime) / 1000);

    const btnNext = document.getElementById('btn-next-q');
    btnNext.disabled = true;

    try {
        const response = await fetch('/api/iq/next', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: activeSessionId,
                answer: isTimeout ? null : selectedOptionValue,
                time_taken: timeTaken
            })
        });

        const data = await response.json();

        // 1-SECOND VISUAL FEEDBACK: GREEN for correct answer, RED for wrong answer
        const allBtns = document.querySelectorAll('.iq-option-btn');
        allBtns.forEach(btn => {
            btn.disabled = true;
            const val = btn.getAttribute('data-option-val');

            if (val === data.correct_answer) {
                // Highlight Correct GREEN
                btn.className = 'iq-option-btn p-4 rounded-xl border-2 border-emerald-500 bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-left font-bold flex items-center justify-between w-full shadow-md';
            } else if (val === selectedOptionValue && !data.is_correct) {
                // Highlight Wrong RED
                btn.className = 'iq-option-btn p-4 rounded-xl border-2 border-rose-500 bg-rose-500/20 text-rose-600 dark:text-rose-400 text-left font-bold flex items-center justify-between w-full shadow-md';
            }
        });

        // Auto-advance to next question after 1 second delay
        setTimeout(() => {
            if (data.is_completed) {
                window.location.href = data.redirect_url;
            } else if (data.success) {
                renderQuestion(data.next_question_data);
            } else {
                alert(data.error || 'Failed to submit answer.');
            }
        }, 1000);

    } catch (err) {
        alert('Network error submitting answer.');
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
}
