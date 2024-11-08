/*
  Create your javascript functions for Project 1 here, using JQuery syntax to manipulate the DOM...
*/
$('#swapButton').click(function() {
  const firstDivId = $('#from').val();
  const secondDivId = $('#to').val();

  const $firstDiv = $('#' + firstDivId);
  const $secondDiv = $('#' + secondDivId);

  if ($firstDiv.length && $secondDiv.length) {
    const firstDivContent = $firstDiv.html();
    const secondDivContent = $secondDiv.html();

    $firstDiv.html(secondDivContent);
    $secondDiv.html(firstDivContent);
  } else {
    alert("One or both of the div IDs entered do not exist.");
  }
});

$('#resetButton').click(function() {
  location.reload();
});

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      let cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          let cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
      if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
          // Only send the token to relative URLs (i.e., same-origin requests)
          xhr.setRequestHeader("X-CSRFToken", csrftoken);
      }
  }
});

