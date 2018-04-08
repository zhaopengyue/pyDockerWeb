$(document).ready(
    function () {
        var common_menus_node = document.getElementById('common-menus-node');
        var cluster_id = window.location.host.split(':')[0];
        $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/common/node/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    for(var i=0; i<resful['message'].length; i++) {
                        if(! resful['message'][i]['status']) {
                            continue;
                        }
                        var li = document.createElement('li');
                        var a = document.createElement('a');
                        a.setAttribute('href', 'node.html?node=' + resful['message'][i]['name']);
                        a.innerHTML = resful['message'][i]['name'];
                        li.appendChild(a);
                        common_menus_node.appendChild(li);
                    }
                }
                else {
                    toastr.error(resful['message']);
                }
            }
        });
    }
);

function get_obj() {
    var ob=eval(row);
    var property="";
　　for(var p in ob){
　　  property+=p+"\n";
　　}
　　alert(property);
}