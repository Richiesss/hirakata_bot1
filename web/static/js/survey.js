// アンケートフォームのJavaScript

document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('surveyForm');
    const opinionTextarea = document.getElementById('opinion');
    const charCount = document.getElementById('charCount');

    // 文字数カウント
    if (opinionTextarea && charCount) {
        opinionTextarea.addEventListener('input', function () {
            const count = this.value.length;
            charCount.textContent = count;

            // 制限に近づいたら色を変更
            if (count > 900) {
                charCount.style.color = '#e74c3c';
            } else if (count > 700) {
                charCount.style.color = '#f39c12';
            } else {
                charCount.style.color = '#667eea';
            }
        });
    }

    // フォーム送信時の確認
    if (form) {
        form.addEventListener('submit', function (e) {
            const category = document.getElementById('category').value;
            const opinion = opinionTextarea.value.trim();

            if (!category) {
                e.preventDefault();
                alert('カテゴリを選択してください');
                return false;
            }

            if (!opinion) {
                e.preventDefault();
                alert('ご意見を入力してください');
                return false;
            }

            // 確認ダイアログ
            if (!confirm('この内容で送信してもよろしいですか？')) {
                e.preventDefault();
                return false;
            }
        });
    }
});
