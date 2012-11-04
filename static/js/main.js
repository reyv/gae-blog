//Main Page
$(document).ready(function (){
  var text = $('.page').text();

  if(text=='home'){
    $('.top_menu > li:nth-child(1)').addClass('active');
  }else if (text=='about'){
    $('.top_menu > li:nth-child(2)').addClass('active');
  }else if(text=='contact'){
    $('.top_menu > li:nth-child(3)').addClass('active');
  }else if (text=='login'){
    $('.top_menu > li:nth-child(4)').addClass('active');
  }
});

//Back button for Blog Post Preview Page
$(document).ready(function(){
    $('#preview-back').on('click', function(){
        parent.history.back();
        return false;
    });
});
