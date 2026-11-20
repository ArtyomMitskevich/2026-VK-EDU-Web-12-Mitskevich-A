// Django проверяет CSRF-токен и права пользователя для каждого запроса.
async function postForm(url, fields) {
    const token = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const response = await fetch(url, {
        method: 'POST',
        mode: 'same-origin',
        headers: {'X-CSRFToken': token},
        body: new URLSearchParams(fields)
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Не удалось сохранить изменение.');
    return data;
}

for (const box of document.querySelectorAll('[data-vote-url]')) {
    box.addEventListener('click', async (event) => {
        const button = event.target.closest('button[data-value]');
        if (!button || box.dataset.busy) return;
        box.dataset.busy = '1';
        try {
            const data = await postForm(box.dataset.voteUrl, {value: button.dataset.value});
            box.querySelector('.score').textContent = data.rating;
            for (const item of box.querySelectorAll('button')) {
                item.disabled = Number(item.dataset.value) === data.value;
                item.title = item.disabled ? 'Вы уже поставили эту оценку' : '';
            }
        } catch (error) {
            alert(error.message);
        } finally {
            delete box.dataset.busy;
        }
    });
}

const answers = document.querySelector('#answers');
if (answers) {
    answers.addEventListener('click', async (event) => {
        const button = event.target.closest('[data-correct-url]');
        if (!button || answers.dataset.busy) return;
        answers.dataset.busy = '1';
        try {
            const data = await postForm(button.dataset.correctUrl, {answer: button.dataset.answer});
            for (const item of answers.querySelectorAll('[data-correct-url]')) {
                const selected = Number(item.dataset.answer) === data.answer && data.is_correct;
                item.setAttribute('aria-pressed', selected);
                item.classList.toggle('is-correct', selected);
                item.closest('article').classList.toggle('answer-accepted', selected);
                item.textContent = selected ? '✓ Правильный ответ' : 'Отметить как правильный';
            }
        } catch (error) {
            alert(error.message);
        } finally {
            delete answers.dataset.busy;
        }
    });
}
