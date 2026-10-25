
let arrow = document.querySelectorAll(".arrow");
for (var i = 0; i < arrow.length; i++) {
  arrow[i].addEventListener("click", (e) => {
    let arrowParent = e.target.parentElement.parentElement;//selecting main parent of arrow
    arrowParent.classList.toggle("showMenu");
  });
}
let sidebar = document.querySelector(".sidebar");
let sidebarBtn = document.querySelector(".bx-menu");

$(function () {
  var backdrop = $('#sidebar-backdrop');

  // Start with sidebar collapsed so content gets full width
  $('.sidebar').addClass('close');

  function updateBackdrop() {
    if ($('.sidebar').hasClass('close')) {
      backdrop.removeClass('active');
    } else {
      backdrop.addClass('active');
    }
  }

  resizeScreen();
  $(window).resize(function(){
    resizeScreen();
  });

  $('.bx-menu').click(function(){
    if(document.body.clientWidth > 400){
      $('.sidebar').toggleClass('close');
    }else{
      $('.sidebar').toggleClass('small-screen');
    }
    updateBackdrop();
  });

  // Clicking the backdrop closes the sidebar
  backdrop.click(function(){
    $('.sidebar').addClass('close');
    updateBackdrop();
  });

  function resizeScreen() {
    if(document.body.clientWidth < 400){
      $('.sidebar').addClass('close');
    }
    // Always start collapsed — don't auto-expand on resize
    updateBackdrop();
  }
});
