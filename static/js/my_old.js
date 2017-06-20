function recalc(volume) {
    var price;
    var pay_vol;
    $('li').each(function(i,o) {
        price = $(this).find('.price').html();
        if ( price > 0 ) {
            pay_vol = volume/price;
            pay_vol = pay_vol.toPrecision(5);
            pay_vol = '= ' + pay_vol
        } else { pay_vol = '---'; }
        $(this).find('.pay_vol').html(pay_vol + ' ' +$(this).find('.abbrev').html());
    });
}

function get_phobe(obj) {
    var phone = obj.value;
    if (phone.length<1) return;
    var v;
    digits = "0123456789";
    var str = "";
    for ( i = 0; i < phone.length; i++) {
        if (digits.indexOf(phone.charAt(i)) >= 0) {
            str = str + phone.charAt(i);
        }
    }
    if ( str.length != 10 ) {
        alert("Введите Ваш номер телефона в виде:\n 888-777-55-33 или (901)234-34-12\n 809.876.5431 или 2345678791\n Должно быть 10 цифр");
        obj.focus();
    }
    $(obj).val(str);
    //$('#prompt').html(str);
    //ajax('phone_check', ['phone'], 'phone_resp');
}
function ph_clear() {
    var obj = $('#phone_val');
    $(obj).val('');
}
recalc(100);


(function(){  // анонимная функция (function(){ })(), чтобы переменные "a" и "b" не стали глобальными
    var a = document.querySelector('#aside1'), b = null;  // селектор блока, который нужно закрепить
    window.addEventListener('scroll', Ascroll, false);
    document.body.addEventListener('scroll', Ascroll, false);  // если у html и body высота равна 100%
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
})()
