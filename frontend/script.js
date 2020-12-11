'use strict';

var tinderContainer = document.querySelector('.tinder');
var allCards = document.querySelectorAll('.tinder--card');
var nope = document.getElementById('nope');
var love = document.getElementById('love');


function initCards(card, index) {
  var newCards = document.querySelectorAll('.tinder--card:not(.removed)');

  newCards.forEach(function (card, index) {
    card.style.zIndex = allCards.length - index;
    card.style.transform = 'scale(' + (20 - index) / 20 + ') translateY(-' + 30 * index + 'px)';
    card.style.opacity = (10 - index) / 10;
  });
  
  tinderContainer.classList.add('loaded');
}

initCards();


const nopeClick = async () => {
	var user="krishna";
	const response = await fetch('http://34.120.175.58/getNext/' + user, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  });
 
  const myJson = await response.json(); //extract JSON from the http response
  console.log(myJson);
  var img = document.getElementById('image');
  var name = document.getElementById('name');
  var desc = document.getElementById('description');
  var price = document.getElementById('price');
  
  img.setAttribute("src", myJson['url']);
  name.innerHTML = myJson['foodName']
  desc.innerHTML = myJson['description']
  price.innerHTML = myJson['price']
}

