$(document).ready(function () {
    // 获取顶端信息
    var cluster_id = window.location.host.split(':')[0];
    $.ajax({
        data: JSON.stringify({'cluster_id': cluster_id}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/index/top/',
        sync: true,
        success: function (resful, status) {
            if(status && resful['status']) {
                document.getElementById('index-top-cpu').innerText = resful['message']['cpu'];
                document.getElementById('index-top-mem').innerText = resful['message']['mem'];
                document.getElementById('index-top-disk').innerText = resful['message']['disk'];
                document.getElementById('index-top-task').innerText = resful['message']['task'];
                document.getElementById('index-top-image').innerText = resful['message']['image'];
                document.getElementById('index-top-node').innerText = resful['message']['node'];
            }
            else {
                toastr.error(resful['message']);
            }
        }
    });
    // 创建表格
    $.ajax({
        data: JSON.stringify({'cluster_id': cluster_id}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/index/node/',
        sync: true,
        success: function (resful, status) {
            if(status && resful['status']) {
                $("#index-table-node").DataTable({
                    data: resful['message'],
                    destroy: true,
                    scrollY: "1000px",
                        scrollCollapse: true
                })
            }
            else {
                toastr.error(resful['message'])
            }
        }
    });
});