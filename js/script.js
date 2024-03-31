const no_avg = ['333mbf', '333mbo'];

function recalcAlternating() {
    var evts = document.getElementsByClassName('evt-active');
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

var isNotCountryTogglePage = ! document.getElementById('nonDEswitch');
if (isNotCountryTogglePage == false) {
    var nonDEswitch = document.getElementById('nonDEswitch');
    nonDEswitch.addEventListener('change', toggle);
}

function showEvt(ev = '333') {
    // remove active, add hidden
    const wasActive = document.querySelectorAll('.evt-active');
    for (var i = 0, len = wasActive.length; i < len; i++) {
        wasActive[i].classList.remove("evt-active");
        wasActive[i].classList.add("evt-hidden");
    }
    // for the chosen evt, the other way around
    var makeActiveSin = document.getElementsByClassName('sin-'+ev);
    if (!no_avg.includes(ev)) {
        var makeActiveAvg = document.getElementsByClassName('avg-'+ev);
    }
    makeActiveSin[0].classList.remove("evt-hidden");
    makeActiveSin[0].classList.add("evt-active");
    if (!no_avg.includes(ev)) {
        makeActiveAvg[0].classList.remove("evt-hidden");
        makeActiveAvg[0].classList.add("evt-active");
    }
    
    const wasActiveBtn = document.querySelectorAll('.btn-active');
    for (var i = 0, len = wasActiveBtn.length; i < len; i++) {
        wasActiveBtn[i].classList.remove("btn-active");
    }
    const makeActiveBtn = document.getElementById('btn-'+ev);
    makeActiveBtn.classList.add("btn-active");
    
    recalcAlternating();
}
