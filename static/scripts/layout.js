const sidebar = document.getElementById('sidebar');
const toggleButton = document.getElementById('toggleSidebar');
const overlay = document.getElementById('overlay');

function toggleSidebar() {
    // Переключаем классы у сайдбара и overlay
    sidebar.classList.toggle('-translate-x-full');  // Переключаем скрытие/показ сайдбара
    overlay.classList.toggle('hidden');             // Переключаем видимость overlay
}

// Обработчик события для кнопки сайдбара
toggleButton.addEventListener('click', toggleSidebar);

// Обработчик для клика на overlay (закрытие сайдбара при клике на затемнение)
overlay.addEventListener('click', toggleSidebar);

function showLoginOrRegister(modal) {
    // Показываем форму входа и скрываем форму регистрации
    if (modal === "login") {
        document.getElementById('login-form').classList.remove('hidden');
        document.getElementById('register-form').classList.add('hidden');

        // Добавляем outline для активной вкладки "Вход"
        document.getElementById('login-tab').classList.add('text-sky-500');
        document.getElementById('register-tab').classList.remove('text-sky-500');
    }

    if (modal === "register") {
        // Показываем форму регистрации и скрываем форму входа
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('register-form').classList.remove('hidden');

        // Добавляем outline для активной вкладки "Регистрация"
        document.getElementById('register-tab').classList.add('text-sky-500');
        document.getElementById('login-tab').classList.remove('text-sky-500');
    }
}