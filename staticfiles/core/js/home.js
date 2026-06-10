document.addEventListener('DOMContentLoaded', function () {
    initLanguageCookie();
    initCookieConsent();
    initMobileMenu();
    initHeroSlider();
    initAboutSlider();
    initFormatsBook();
    initMusicPlayer();
    initReservationModal();
    initReservationFeedbackModal();
});

// '''Función initMobileMenu. Gestiona la apertura y cierre del menú móvil de navegación.'''
function initMobileMenu() {
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    if (!navToggle || !navLinks) {
        return;
    }

    navToggle.addEventListener('click', function () {
        navLinks.classList.toggle('is-open');
        navToggle.classList.toggle('is-open');
    });

    const links = navLinks.querySelectorAll('a');

    links.forEach(function (link) {
        link.addEventListener('click', function () {
            navLinks.classList.remove('is-open');
            navToggle.classList.remove('is-open');
        });
    });
}

// '''Función initLanguageCookie. Guarda y recupera el idioma elegido por el usuario mediante cookies.'''
function initLanguageCookie() {
    const languageLinks = document.querySelectorAll('[data-language-code]');
    const languageCookieName = 'veu_selected_language';
    const availableLanguages = ['es', 'ca', 'en'];

    // '''Función getCookie. Obtiene el valor de una cookie por su nombre.'''
    function getCookie(name) {
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.indexOf(name + '=') === 0) {
                return cookie.substring(name.length + 1);
            }
        }

        return null;
    }

    // '''Función setCookie. Crea o actualiza una cookie con una duración determinada.'''
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));

        document.cookie = name + '=' + value +
            '; expires=' + date.toUTCString() +
            '; path=/' +
            '; SameSite=Lax';
    }

    // '''Función getCurrentLanguageFromPath. Obtiene el idioma actual a partir de la URL.'''
    function getCurrentLanguageFromPath() {
        const pathParts = window.location.pathname.split('/').filter(Boolean);

        if (!pathParts.length) {
            return null;
        }

        if (availableLanguages.indexOf(pathParts[0]) !== -1) {
            return pathParts[0];
        }

        return null;
    }

    // '''Función redirectToSavedLanguageIfNeeded. Redirige al idioma guardado si la URL no contiene idioma.'''
    function redirectToSavedLanguageIfNeeded() {
        const savedLanguage = getCookie(languageCookieName);
        const currentLanguage = getCurrentLanguageFromPath();

        if (!savedLanguage || availableLanguages.indexOf(savedLanguage) === -1) {
            return;
        }

        if (currentLanguage) {
            return;
        }

        window.location.href = '/' + savedLanguage + '/';
    }

    languageLinks.forEach(function (link) {
        link.addEventListener('click', function () {
            const selectedLanguage = link.dataset.languageCode;

            if (!selectedLanguage || availableLanguages.indexOf(selectedLanguage) === -1) {
                return;
            }

            setCookie(languageCookieName, selectedLanguage, 180);
        });
    });

    const currentLanguage = getCurrentLanguageFromPath();

    if (currentLanguage) {
        setCookie(languageCookieName, currentLanguage, 180);
    } else {
        redirectToSavedLanguageIfNeeded();
    }
}

// '''Función initHeroSlider. Inicializa el carrusel automático de imágenes del hero.'''
function initHeroSlider() {
    const heroImage = document.getElementById('heroImage');
    const dataElement = document.getElementById('hero-images-data');

    if (!heroImage || !dataElement) {
        return;
    }

    let heroImages = [];

    try {
        heroImages = JSON.parse(dataElement.textContent);
    } catch (error) {
        heroImages = [];
    }

    if (heroImages.length <= 1) {
        return;
    }

    heroImage.style.transition = 'opacity 0.55s ease, transform 1.2s ease';

    let currentIndex = 0;

    window.setInterval(function () {
        currentIndex = (currentIndex + 1) % heroImages.length;

        heroImage.style.opacity = '0';
        heroImage.style.transform = 'scale(1.03)';

        window.setTimeout(function () {
            heroImage.src = heroImages[currentIndex].image;
            heroImage.alt = heroImages[currentIndex].alt || 'Imagen hero';

            heroImage.onload = function () {
                heroImage.style.opacity = '1';
                heroImage.style.transform = 'scale(1)';
            };
        }, 550);
    }, 5000);
}

// '''Función initAboutSlider. Inicializa el carrusel automático de imágenes de la sección About.'''
function initAboutSlider() {
    const aboutImage = document.getElementById('aboutImage');
    const dataElement = document.getElementById('about-images-data');

    if (!aboutImage || !dataElement) {
        return;
    }

    let aboutImages = [];

    try {
        aboutImages = JSON.parse(dataElement.textContent);
    } catch (error) {
        aboutImages = [];
    }

    if (aboutImages.length <= 1) {
        return;
    }

    aboutImage.style.transition = 'opacity 0.55s ease, transform 1.2s ease';

    let currentIndex = 0;

    window.setInterval(function () {
        currentIndex = (currentIndex + 1) % aboutImages.length;

        aboutImage.style.opacity = '0';
        aboutImage.style.transform = 'scale(1.03)';

        window.setTimeout(function () {
            aboutImage.src = aboutImages[currentIndex].image;
            aboutImage.alt = aboutImages[currentIndex].alt || 'Imagen about';

            aboutImage.onload = function () {
                aboutImage.style.opacity = '1';
                aboutImage.style.transform = 'scale(1)';
            };
        }, 550);
    }, 6000);
}

// '''Función initFormatsBook. Inicializa el libro interactivo de formatos musicales.'''
function initFormatsBook() {
    const dataElement = document.getElementById('formats-data');

    if (!dataElement) {
        return;
    }

    let formats = [];

    try {
        formats = JSON.parse(dataElement.textContent);
    } catch (error) {
        formats = [];
    }

    if (!formats.length) {
        return;
    }

    const bookStaticLeft = document.getElementById('bookStaticLeft');
    const bookStaticRight = document.getElementById('bookStaticRight');
    const bookFlipPage = document.getElementById('bookFlipPage');
    const bookFaceFront = document.getElementById('bookFaceFront');
    const bookFaceBack = document.getElementById('bookFaceBack');
    const prevButton = document.getElementById('bookPrev');
    const nextButton = document.getElementById('bookNext');

    if (!bookStaticLeft || !bookStaticRight || !bookFlipPage || !bookFaceFront || !bookFaceBack) {
        return;
    }

    let currentIndex = 0;
    let isAnimating = false;
    let fallbackTimer = null;

    // '''Función createTextPage. Crea la página de texto de un formato musical.'''
    function createTextPage(format) {
        const wrapper = document.createElement('div');
        wrapper.className = 'book-page-copy';

        const title = document.createElement('h3');
        title.textContent = format.title || '';

        const description = document.createElement('p');
        description.textContent = format.description || '';

        wrapper.appendChild(title);
        wrapper.appendChild(description);

        return wrapper;
    }

    // '''Función createImagePage. Crea la página de imagen de un formato musical.'''
    function createImagePage(format) {
        const wrapper = document.createElement('div');
        wrapper.className = 'book-page-image';

        if (format.image) {
            const image = document.createElement('img');
            image.src = format.image;
            image.alt = format.alt || format.title || 'Formato musical';
            wrapper.appendChild(image);
        } else {
            const empty = document.createElement('div');
            empty.className = 'book-image-empty';
            empty.textContent = 'Sin imagen';
            wrapper.appendChild(empty);
        }

        return wrapper;
    }

    // '''Función setPageContent. Sustituye el contenido de una página del libro.'''
    function setPageContent(element, content) {
        element.innerHTML = '';
        element.appendChild(content);
    }

    // '''Función renderStatic. Pinta las páginas visibles del libro sin animación.'''
    function renderStatic(format) {
        setPageContent(bookStaticLeft, createTextPage(format));
        setPageContent(bookStaticRight, createImagePage(format));
    }

    // '''Función cleanFlipPage. Limpia las clases y el contenido de la página animada.'''
    function cleanFlipPage() {
        bookFlipPage.classList.remove('is-ready');
        bookFlipPage.classList.remove('is-flipping');
        bookFlipPage.classList.remove('is-forward');
        bookFlipPage.classList.remove('is-backward');
        bookFaceFront.innerHTML = '';
        bookFaceBack.innerHTML = '';
    }

    // '''Función setButtonsDisabled. Activa o desactiva los botones del libro durante la animación.'''
    function setButtonsDisabled(disabled) {
        if (prevButton) {
            prevButton.disabled = disabled;
        }

        if (nextButton) {
            nextButton.disabled = disabled;
        }
    }

    // '''Función prepareForward. Prepara el contenido visual para pasar a la página siguiente.'''
    function prepareForward(currentFormat, nextFormat) {
        setPageContent(bookStaticLeft, createTextPage(currentFormat));
        setPageContent(bookStaticRight, createImagePage(nextFormat));
        setPageContent(bookFaceFront, createImagePage(currentFormat));
        setPageContent(bookFaceBack, createTextPage(nextFormat));
        bookFlipPage.classList.add('is-forward');
    }

    // '''Función prepareBackward. Prepara el contenido visual para volver a la página anterior.'''
    function prepareBackward(currentFormat, previousFormat) {
        setPageContent(bookStaticLeft, createTextPage(previousFormat));
        setPageContent(bookStaticRight, createImagePage(currentFormat));
        setPageContent(bookFaceFront, createTextPage(currentFormat));
        setPageContent(bookFaceBack, createImagePage(previousFormat));
        bookFlipPage.classList.add('is-backward');
    }

    // '''Función finishAnimation. Finaliza la animación del libro y actualiza el formato actual.'''
    function finishAnimation(nextFormat, nextIndex) {
        if (fallbackTimer) {
            window.clearTimeout(fallbackTimer);
            fallbackTimer = null;
        }

        renderStatic(nextFormat);
        cleanFlipPage();
        currentIndex = nextIndex;
        isAnimating = false;
        setButtonsDisabled(false);
    }

    // '''Función goToIndex. Cambia a un formato concreto aplicando la animación indicada.'''
    function goToIndex(nextIndex, direction) {
        if (isAnimating || nextIndex === currentIndex) {
            return;
        }

        isAnimating = true;
        setButtonsDisabled(true);
        cleanFlipPage();

        const currentFormat = formats[currentIndex];
        const nextFormat = formats[nextIndex];

        if (direction === 'forward') {
            prepareForward(currentFormat, nextFormat);
        } else {
            prepareBackward(currentFormat, nextFormat);
        }

        bookFlipPage.classList.add('is-ready');

        void bookFlipPage.offsetWidth;

        window.requestAnimationFrame(function () {
            bookFlipPage.classList.add('is-flipping');
        });

        const onTransitionEnd = function (event) {
            if (event.target !== bookFlipPage || event.propertyName !== 'transform') {
                return;
            }

            bookFlipPage.removeEventListener('transitionend', onTransitionEnd);
            finishAnimation(nextFormat, nextIndex);
        };

        bookFlipPage.addEventListener('transitionend', onTransitionEnd);

        fallbackTimer = window.setTimeout(function () {
            bookFlipPage.removeEventListener('transitionend', onTransitionEnd);
            finishAnimation(nextFormat, nextIndex);
        }, 1450);
    }

    // '''Función nextFormat. Avanza al siguiente formato del libro.'''
    function nextFormat() {
        const nextIndex = (currentIndex + 1) % formats.length;
        goToIndex(nextIndex, 'forward');
    }

    // '''Función prevFormat. Retrocede al formato anterior del libro.'''
    function prevFormat() {
        const previousIndex = (currentIndex - 1 + formats.length) % formats.length;
        goToIndex(previousIndex, 'backward');
    }

    // '''Función prepareClickablePages. Permite cambiar de formato haciendo clic en las páginas del libro.'''
    function prepareClickablePages() {
        bookStaticLeft.classList.add('book-static-page-clickable');
        bookStaticRight.classList.add('book-static-page-clickable');

        bookStaticLeft.setAttribute('role', 'button');
        bookStaticRight.setAttribute('role', 'button');
        bookStaticLeft.setAttribute('tabindex', '0');
        bookStaticRight.setAttribute('tabindex', '0');
        bookStaticLeft.setAttribute('aria-label', 'Formato anterior');
        bookStaticRight.setAttribute('aria-label', 'Formato siguiente');

        bookStaticLeft.addEventListener('click', function () {
            prevFormat();
        });

        bookStaticRight.addEventListener('click', function () {
            nextFormat();
        });

        bookStaticLeft.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                prevFormat();
            }
        });

        bookStaticRight.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                nextFormat();
            }
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', function () {
            nextFormat();
        });
    }

    if (prevButton) {
        prevButton.addEventListener('click', function () {
            prevFormat();
        });
    }

    prepareClickablePages();
    renderStatic(formats[currentIndex]);
}

// '''Función initMusicPlayer. Gestiona el reproductor de Spotify y el cambio de canción activa.'''
function initMusicPlayer() {
    const spotifyPlayer = document.getElementById('spotifyPlayer');
    const trackTitle = document.getElementById('musicTrackTitle');
    const trackButtons = document.querySelectorAll('.music-track-button');

    if (!spotifyPlayer || !trackButtons.length) {
        return;
    }

    trackButtons.forEach(function (button) {
        button.addEventListener('click', function () {
            const spotifyUrl = button.dataset.spotifyUrl;
            const title = button.dataset.trackTitle;

            if (!spotifyUrl) {
                return;
            }

            spotifyPlayer.dataset.src = spotifyUrl;

            if (document.cookie.indexOf('veu_cookie_consent=accepted') !== -1) {
                spotifyPlayer.src = spotifyUrl;
            }

            if (trackTitle && title) {
                trackTitle.textContent = title;
            }

            trackButtons.forEach(function (currentButton) {
                currentButton.classList.remove('is-active');
            });

            button.classList.add('is-active');
        });
    });
}

// '''Función initCookieConsent. Gestiona el aviso de cookies y la carga o bloqueo del reproductor de Spotify.'''
function initCookieConsent() {
    const cookieBanner = document.getElementById('cookieBanner');
    const acceptButton = document.getElementById('cookieAccept');
    const rejectButton = document.getElementById('cookieReject');
    const preferencesButton = document.getElementById('cookiePreferences');
    const acceptSpotifyButtons = document.querySelectorAll('.js-accept-cookies');

    const consentCookieName = 'veu_cookie_consent';

    // '''Función getCookie. Obtiene el valor de una cookie por su nombre.'''
    function getCookie(name) {
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.indexOf(name + '=') === 0) {
                return cookie.substring(name.length + 1);
            }
        }

        return null;
    }

    // '''Función setCookie. Crea o actualiza una cookie con una duración determinada.'''
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));

        document.cookie = name + '=' + value +
            '; expires=' + date.toUTCString() +
            '; path=/' +
            '; SameSite=Lax';
    }

    // '''Función showBanner. Muestra el aviso de cookies.'''
    function showBanner() {
        if (!cookieBanner) {
            return;
        }

        cookieBanner.classList.add('is-visible');
        cookieBanner.setAttribute('aria-hidden', 'false');
    }

    // '''Función hideBanner. Oculta el aviso de cookies.'''
    function hideBanner() {
        if (!cookieBanner) {
            return;
        }

        cookieBanner.classList.remove('is-visible');
        cookieBanner.setAttribute('aria-hidden', 'true');
    }

    // '''Función loadSpotifyPlayers. Carga el reproductor de Spotify cuando las cookies están aceptadas.'''
    function loadSpotifyPlayers() {
        const spotifyPlayer = document.getElementById('spotifyPlayer');
        const spotifyPlaceholder = document.getElementById('spotifyCookiePlaceholder');

        if (!spotifyPlayer) {
            return;
        }

        const spotifyUrl = spotifyPlayer.dataset.src;

        if (spotifyUrl && !spotifyPlayer.src) {
            spotifyPlayer.src = spotifyUrl;
        }

        spotifyPlayer.classList.remove('spotify-player-hidden');

        if (spotifyPlaceholder) {
            spotifyPlaceholder.classList.add('is-hidden');
        }
    }

    // '''Función unloadSpotifyPlayers. Desactiva el reproductor de Spotify cuando las cookies no están aceptadas.'''
    function unloadSpotifyPlayers() {
        const spotifyPlayer = document.getElementById('spotifyPlayer');
        const spotifyPlaceholder = document.getElementById('spotifyCookiePlaceholder');

        if (!spotifyPlayer) {
            return;
        }

        spotifyPlayer.removeAttribute('src');
        spotifyPlayer.classList.add('spotify-player-hidden');

        if (spotifyPlaceholder) {
            spotifyPlaceholder.classList.remove('is-hidden');
        }
    }

    // '''Función acceptCookies. Guarda la aceptación de cookies y activa Spotify.'''
    function acceptCookies() {
        setCookie(consentCookieName, 'accepted', 180);
        hideBanner();
        loadSpotifyPlayers();
    }

    // '''Función rejectCookies. Guarda el rechazo de cookies y desactiva Spotify.'''
    function rejectCookies() {
        setCookie(consentCookieName, 'rejected', 180);
        hideBanner();
        unloadSpotifyPlayers();
    }

    const savedConsent = getCookie(consentCookieName);

    if (savedConsent === 'accepted') {
        loadSpotifyPlayers();
    } else if (savedConsent === 'rejected') {
        unloadSpotifyPlayers();
    } else {
        showBanner();
        unloadSpotifyPlayers();
    }

    if (acceptButton) {
        acceptButton.addEventListener('click', acceptCookies);
    }

    if (rejectButton) {
        rejectButton.addEventListener('click', rejectCookies);
    }

    if (preferencesButton) {
        preferencesButton.addEventListener('click', function () {
            showBanner();
        });
    }

    acceptSpotifyButtons.forEach(function (button) {
        button.addEventListener('click', acceptCookies);
    });
}

// '''Función initReservationModal. Gestiona la apertura y cierre del modal de reserva.'''
function initReservationModal() {
    const reservationModal = document.getElementById('reservationModal');
    const openReservationButtons = document.querySelectorAll('.js-open-reservation');
    const closeReservationButtons = document.querySelectorAll('.js-close-reservation');

    if (!reservationModal) {
        return;
    }

    // '''Función openReservationModal. Abre el modal de reserva.'''
    function openReservationModal(event) {
        if (event) {
            event.preventDefault();
        }

        reservationModal.classList.add('is-open');
        reservationModal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('reservation-modal-open');
    }

    // '''Función closeReservationModal. Cierra el modal de reserva.'''
    function closeReservationModal(event) {
        if (event) {
            event.preventDefault();
        }

        reservationModal.classList.remove('is-open');
        reservationModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('reservation-modal-open');
    }

    openReservationButtons.forEach(function (button) {
        button.addEventListener('click', openReservationModal);
    });

    closeReservationButtons.forEach(function (button) {
        button.addEventListener('click', closeReservationModal);
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
            closeReservationModal();
        }
    });
}

// '''Función initReservationFeedbackModal. Gestiona el cierre del modal de confirmación de reserva.'''
function initReservationFeedbackModal() {
    const feedbackModal = document.getElementById('reservationFeedbackModal');
    const closeFeedbackButtons = document.querySelectorAll('.js-close-feedback');

    if (!feedbackModal) {
        return;
    }

    // '''Función closeFeedbackModal. Cierra el modal de confirmación de reserva.'''
    function closeFeedbackModal(event) {
        if (event) {
            event.preventDefault();
        }

        feedbackModal.classList.remove('is-open');
        feedbackModal.setAttribute('aria-hidden', 'true');

        if (!document.querySelector('.reservation-modal.is-open')) {
            document.body.classList.remove('reservation-modal-open');
        }
    }

    closeFeedbackButtons.forEach(function (button) {
        button.addEventListener('click', closeFeedbackModal);
    });

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && feedbackModal.classList.contains('is-open')) {
            closeFeedbackModal();
        }
    });
}