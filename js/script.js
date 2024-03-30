function recalcAlternating() {
    var evts = document.getElementsByClassName('evt');
    for (var a = 0, leng = evts.length; a < leng; a++) {
        var visi_count = 0;
        var bgColRows = evts[a].getElementsByClassName('bgColRow');
        for (var j = 0, lengt = bgColRows.length; j < lengt; j++) {
            if (bgColRows[j].style.display != 'none') {
                if (visi_count % 2 != 0) {
                    bgColRows[j].style.backgroundColor = '#f2f2f2';
                }
                else {
                    bgColRows[j].style.backgroundColor = '#ffffff';
                }
                visi_count = visi_count + 1;
            }
        }
    }
}


function toggle (e) {
    var self = e.target,
        toggleClass = '.' + self.value,
        toToggle = document.querySelectorAll(toggleClass);
    for (var i = 0, len = toToggle.length; i < len; i++) {
        toToggle[i].style.display = self.checked ? 'table-row' : 'none';
    }    
    recalcAlternating();
}

var nonDEswitch = document.getElementById('nonDEswitch');
nonDEswitch.addEventListener('change', toggle);
