let interval = 1000 * 10

function updateClips(){
    $.ajax({
        url: "/clips/container",
        success: function(response){
            $('.clip-container').html(response);
        }
    });
}
updateClips()
setInterval(updateClips, interval);