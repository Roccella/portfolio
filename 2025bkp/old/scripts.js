document.addEventListener('DOMContentLoaded', function () {
    const options = {
        type: 'slide',
        drag: 'free',
        snap: true,
        rewind: true,
        gap: '1rem',
        padding: '3rem',
        autoHeight: true,
        perPage: 4,
        breakpoints: {
            1360: {
                perPage: 3,
            },
            940: {
                perPage: 2,
            },
            520: {
                perPage: 1,
            },
        },
    };

    // Select all elements with IDs that match the pattern #splideX
    const splideElements = document.querySelectorAll('[id^="splide"]');

    splideElements.forEach((element) => {
        const splide = new Splide(`#${element.id}`, options);
        
        splide.on('mounted', function () {
            splide.refresh();
        });

        splide.mount();
    });
});