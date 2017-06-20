(function(){  // анонимная функция (function(){ })(), чтобы переменные "a" и "b" не стали глобальными
    var a = document.querySelector('#aside1'), b = null;  // селектор блока, который нужно закрепить
    window.addEventListener('scroll', Bscroll, false);
    document.body.addEventListener('scroll', Bscroll, false);  // если у html и body высота равна 100%
    function Ascroll() {
        if (b == null) {  // добавить потомка-обёртку, чтобы убрать зависимость с соседями
            a.innerHTML = '<div>'+a.innerHTML+'</div>';
            b = a.children[0];
      }
            if (a.getBoundingClientRect().top <= 0) { // elem.getBoundingClientRect() возвращает в px координаты элемента относительно верхнего левого угла области просмотра окна браузера
                b.className = 'navbar-fixed-top';
            } else {
                b.className = '';
      }
    }
  var elem1 = $('#aside1');
  //var cs_hght = elem.height(); // высота шапки
  // http://mattweb.ru/moj-blog/javascript-jquery/item/63-fiksiruem-menu-pri-prokrutke-stranitsy
  function Bscroll(){ // http://mattweb.ru/demo/fixed_menu_hide/
      // значение высоты меняется - его тут локально ищем
      var h_mrg1 = 0;    // отступ когда шапка уже не видна
      var h_hght1 = $('#top_line').height(); // высота шапки
      var top1 = $(this).scrollTop();
      if (top1+h_mrg1 < h_hght1) {
       elem1.css('top', (h_hght1-top1));
      } else {
       elem1.css('top', h_mrg1);
      }
    };

    window.addEventListener('resize', myResize, false);
    document.body.addEventListener('resize', myResize, false);
    var elem0 = $('#aside0');
    function myResize(){
        // значение высоты меняется - его тут локально ищем
        // оно и так учитывается браузером var h_hght0 = $('#top_line').height() + $('#aside1').height();
        var h_hght0 = $('#aside1').height();
        elem0.css('margin-top', h_hght0);
    };
    Bscroll();
    myResize();
})()


function recalc(volume, max) {
    //$('#prompt').html(volume);
    if ( max > 0 && volume > max ) {
        volume = max;
        $('#pay_val').val(max);
    }
    var price;
    var pay_vol;
    $('div.sel_xcurr').each(function(i,o) {
        price = $(this).find('.price').html();
        if ( price > 0 ) {
            pay_vol = volume/price;
            pay_vol = pay_vol.toPrecision(5);
            pay_vol = pay_vol;
        } else { pay_vol = '---'; }
        //$(this).find('.pay_vol').html(pay_vol + ' ' +$(this).find('.abbrev').html());
        $(this).find('.pay_vol').html(pay_vol);
    });
}
