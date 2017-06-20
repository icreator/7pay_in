function hasClass(elCls, cls) {
 if (!elCls || !cls) return false
 return (" " + elCls + " ").indexOf(" " + cls + " ") !== -1;
}
function changeClass(o, add, del) {
 var n = "className", cN = (undefined != o[n]) ? o[n] : o, ok = 0
 if ("string" !== typeof cN) return false
 var re = new RegExp('(\\s+|^)' + del + '(\\s+|$)', 'g')
 if (add) /*addClass*/
  if (!hasClass(cN, add)) {cN += " " + add; ok++}
 if (del) /*delClass*/
  if (hasClass(cN, del)) {cN = cN.replace(re, " "); ok++}
 if (!ok) return false
 if ("object" == typeof o) o[n] = cN 
 else return cN
}

(function(){  // анонимная функция (function(){ })(), чтобы переменные "a" и "b" не стали глобальными
    var a = document.querySelector('#aside1'), b = null;  // селектор блока, который нужно закрепить
    window.addEventListener('scroll', Ascroll, false);
    document.body.addEventListener('scroll', Ascroll, false);  // если у html и body высота равна 100%
    function Ascroll() {
        if (b == null) {  // добавить потомка-обёртку, чтобы убрать зависимость с соседями
            /*
            var Sa = getComputedStyle(a, ''), s = '';
            for (var i = 0; i < Sa.length; i++) {  // перечислить стили CSS, которые нужно скопировать с родителя
                if (Sa[i].indexOf('box-sizing') == 0 || Sa[i].indexOf('overflow') == 0 || Sa[i].indexOf('width') == 0 || Sa[i].indexOf('padding') == 0 || Sa[i].indexOf('border') == 0 || Sa[i].indexOf('outline') == 0 || Sa[i].indexOf('box-shadow') == 0 || Sa[i].indexOf('background') == 0) {
                    s += Sa[i] + ': ' +Sa.getPropertyValue(Sa[i]) + '; '
                }
            }
            */
            a.innerHTML = '<div style="'+s+'">'+a.innerHTML+'</div>';
            b = a.children[0];
            //a.style.height = b.getBoundingClientRect().height + 'px';  // если под скользящим элементом есть другие блоки, можно своё значение
            //a.style.padding = '0';
            //a.style.border = '0';  // если элементу присвоен padding или border
      }
            if (a.getBoundingClientRect().top <= 0) { // elem.getBoundingClientRect() возвращает в px координаты элемента относительно верхнего левого угла области просмотра окна браузера
                //b.className = 'sticky';
                b.className = 'navbar-fixed-top';
                //changeClass(a, 'navbar-fixed-top');
            } else {
                //changeClass(a, false, 'navbar-fixed-top');
                b.className = '';
      }
    }
})()
