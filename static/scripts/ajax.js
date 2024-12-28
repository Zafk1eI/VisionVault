$(document).ready(function () {
    $(document).on('click', '#subscribe_button', function () {
        const $button = $(this);
        const channelId = $button.attr('data-user-id');

        $.ajax({
            url: `/subscribe/${channelId}`,
            method: 'POST',
            success: function (response) {
                if (response.success) {
                    $button.text('Вы подписаны');
                    $button.prop('id', 'unsubscribe_button');
                    $button.removeClass('border-sky-500 text-sky-500');
                    $button.addClass('border-gray-500 text-gray-500');
                } else {
                    alert(response.error);
                }
            },
            error: function (xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Ошибка при подписке';
                alert(errorMsg);
            }
        });
    });
});


$(document).ready(function () {
    $(document).on('click', '#unsubscribe_button', function () {
        const $button = $(this);
        const channelId = $button.attr('data-user-id');

        $.ajax({
            url: `/unsubscribe/${channelId}`,
            method: 'POST',
            success: function (response) {
                if (response.success) {
                    $button.text('Подписаться');
                    $button.prop('id', 'subscribe_button');
                    $button.removeClass('border-gray-500 text-gray-500');
                    $button.addClass('border-sky-500 text-sky-500');
                } else {
                    alert(response.error);
                }
            },
            error: function (xhr) {
                const errorMsg = xhr.responseJSON?.error || 'Ошибка при отписке';
                alert(errorMsg);
            }
        });
    });
});

$(document).ready(function () {
    const likeButton = $('#likes');
    const dislikeButton = $('#dislike');
    // Лайк
    $('#likes').click(function () {
        const video_id = $("#video-source").attr('video-id');

        $.ajax({
            url: '/like/' + video_id,
            method: 'POST',
            success: function (response) {
                if (response.success) {
                    if (response.action === 'liked') {
                        likeButton.find('svg').css('fill', '#1485BC');
                        dislikeButton.find('svg').css('fill', 'black');
                    } else if (response.action === 'removed') {
                        likeButton.find('svg').css('fill', 'black');
                    }
                    likeButton.find('span').text(response.likes);
                    dislikeButton.find('span').text(response.dislikes);
                } else {
                    alert(response.error);
                }
            },
            error: function () {
                alert('Ошибка при отправке запроса.');
            }
        });
    });

    $('#dislike').click(function () {
        const video_id = $("#video-source").attr('video-id');

        $.ajax({
            url: '/dislike/' + video_id,
            method: 'POST',
            success: function (response) {
                if (response.success) {
                    if (response.action === 'disliked') {
                        dislikeButton.find('svg').css('fill', '#1485BC');
                        likeButton.find('svg').css('fill', 'black');
                    } else if (response.action === 'removed') {
                        dislikeButton.find('svg').css('fill', 'black');
                    }
                    likeButton.find('span').text(response.likes);
                    dislikeButton.find('span').text(response.dislikes);
                } else {
                    alert(response.error);
                }
            },
            error: function () {
                alert('Ошибка при отправке запроса.');
            }
        });
    });
});

$(document).ready(function () {
    $('#comment-form').on('submit', function (e) {
        e.preventDefault();

        var comment = $('input[name="comment"]').val();
        const video_id = $("#video-source").attr('video-id');
    
        $.ajax({
            url: '/post_comment/' + video_id,
            method: 'POST',
            data: {
                comment: comment
            },
            success: function (response) {
                if (response.success) {
                    $('#message').html('<span style="color: green;">Комментарий успешно добавлен!</span>');
                    $('input[name="comment"]').val('');
                } else {
                    $('#message').html('<span style="color: red;">Ошибка: ' + response.error + '</span>');
                }
            },
            error: function (xhr, status, error) {
                $('#message').html('<span style="color: red;">Произошла ошибка. Попробуйте позже.</span>');
            }
        });
    });
});

$(document).ready(function () {
    var page = 1;
    var per_page = 10; 
    var hasMoreVideos = true;

    function loadRecommendedVideos() {
    if (!hasMoreVideos) return;

        console.log("Loading recommended videos...");
        const video_id = $("#video-source").attr('video-id');

        $.get('/recommendations', { page: page, per_page: per_page, video_id: video_id }, function(data) {
        if (data.videos && data.videos.length > 0) {
            data.videos.forEach(function(video) {
                const videoHtml = `
                    <div id="video-card" class='max-w-[25rem] h-36 rounded-md border-none flex flex-row pt-4'>
                        <div id="img-card" class='relative pr-2'>
                            <a href="/watch/${video.video_id}">
                                <img class='border rounded-lg border-none w-96 h-[120px] relative'
                                    src="/get_thumbnail/${video.video_id}/thumbnail.jpg" alt=' '>
                                <span id="duration"
                                    class="absolute bottom-2 right-2 m-2 p-[2px] bg-black rounded bg-opacity-75 font-sans text-xs text-white">
                                    ${video.duration}
                                </span>
                        </div>
                        <div class="w-full flex flex-col">
                            <span class="text-base font-semibold line-clamp-2">${video.title}</span>
                        </a>
                            <div class='flex flex-col text-gray-500'>
                                <a href="/channel/${video.user.user_id}">
                                <span id='nickname' class='inline-block align-bottom'>${video.user.username}</span>
                                </a>
                                <div class='flex gap-x-1 text-sm font-semibold'>
                                    <span id='views' class="text-nowrap">${video.views} просмотров</span>
                                    <span> • </span>
                                    <span id='times' class="text-nowrap truncate w-12">${video.created_at}</span>
                                </div>
                            </div>
                        </div>
                    </div>`
                $('#video-list').append(videoHtml);
            });
        page++;
    } else {
        hasMoreVideos = false;
        console.log("No more recommended videos to load.");
    }
});

    }
    var debounceTimer;
    $(window).scroll(function () {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 300) {
            clearTimeout(debounceTimer);

            debounceTimer = setTimeout(function () {
                loadRecommendedVideos();
            }, 200);
        }
    });
    loadRecommendedVideos();
});


$(document).ready(function () {
    var page = 1;
    var per_page = 10; 
    var hasMoreComments = true;
    var video_id = $("#video-source").attr('video-id'); 

    function loadComments() {
        if (!hasMoreComments) return;

        console.log("Loading comments...");
        
        $.get('/comments', { page: page, per_page: per_page, video_id: video_id }, function(data) {
            if (data.comments && data.comments.length > 0) {
                data.comments.forEach(function(comment) {
                    const commentHtml = `
                    <div class='flex flex-row gap-2 mt-2'>
                        <img class='w-10 h-10 border rounded-full border-none bg-slate-600' src="/get_photo/${comment.user.photo_url}" alt='avatar'>
                        <div class='flex flex-col w-4/6'>
                            <div class='flex flex-row gap-2'>
                                <span>${comment.user.username}</span>
                                <span class='text-gray-400'>${comment.created_at }</span>
                            </div>
                            <span>${comment.text}</span>
                        </div>
                    </div>`;
                    
                    $('#comments').append(commentHtml);

                });
                page++; 
            } else {
                hasMoreComments = false;
                console.log("No more comments to load.");
            }
        });
    }

    var debounceTimer;
    $(window).scroll(function () {
        if ($(window).scrollTop() + $(window).height() >= $(document).height() - 300) {
            clearTimeout(debounceTimer);

            debounceTimer = setTimeout(function () {
                loadComments();
            }, 200);
        }
    });
});