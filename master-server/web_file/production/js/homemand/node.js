var time = 3;
var cluster_id = window.location.host.split(':')[0];
var maxLength = 30;
// 获取get变量
function getQueryVariable(variable)
{
       var query = window.location.search.substring(1);
       var vars = query.split("&");
       for (var i=0;i<vars.length;i++) {
               var pair = vars[i].split("=");
               if(pair[0] === variable){return pair[1];}
       }
       return(false);
}
// 跳转页面
function ChangeTime() {
      time--;
      if (time <= 0) {
        window.location.href = "/index.html";
      } else {
        setTimeout(ChangeTime, 1000);
      }
}

// 获取服务器列表, 更新下拉框
function get_image_server() {
    $.ajax({
        data: JSON.stringify({}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/node/alive_server_list/',
        sync: false,
        success: function (resful, status) {
            if(status && resful['status']) {
                var temp_test = null;
                var result = resful['message']['message'];
                var select = document.getElementById('node-image-server-select');
                select.innerHTML = '';
                for(var i=0 ; i < result.length; i++) {
                    var option = document.createElement('option');
                    if(i === 0) {
                        option.setAttribute('selected', true);
                        temp_test = result[i][0];
                    }
                    option.setAttribute('name', 'select_node');
                    option.setAttribute('value', result[i][0]);
                    option.innerHTML = result[i][0];
                    select.appendChild(option);
                }
                init_form(temp_test);
            }
            else {
                toastr.error(resful['message'])
            }
        }
    })
}

function select_on_change() {
    if ($('#node-image-server-info').hasClass('dataTable'))
    {
        var dttable = $('#node-image-server-info').dataTable();
        dttable.fnClearTable(); //清空一下table
        dttable.fnDestroy(); //还原初始化了的datatable
    }
    var new_select_node = get_select_node();
    init_form(new_select_node);
}

function Mem(node) {
    var node_mem = echarts.init(document.getElementById('node-mem'));
    var cluster_id = window.location.host.split(':')[0];
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id, 'node': node}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/node/mem/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    result = resful['message']['message'];
                    node_mem.hideLoading();
                    node_mem.setOption({
                        title: {
                            text: '内存占比',
                            left: 'center'
                        },
                        legend: {
                            data: ['活动内存', "空闲内存", "缓存"],
                            // orient: 'vertical',
                            // y: 'center',    //延Y轴居中
                            // x: 'center' //居右显示
                            bottom: 'top'
                        },
                        toolbox: {
                            show: true,
                            feature: {
                                dataView: {readOnly: false},
                                saveAsImage: {}
                            }
                        },
                        series: [
                            {
                                name: '节点内存',
                                type: 'pie',
                                radius: '65%',
                                center: ['50%', '50%'],
                                // animation: false,
                                label:{            //饼图图形上的文本标签
                                    normal:{
                                        show:true,
                                        textStyle : {
                                            fontWeight : 300 ,
                                            fontSize : 16    //文字的字体大小
                                        },
                                        formatter:'{d}%'
                                    }
                                },
                                data: [
                                    {value: result['active_mem'], name: "活动内存"},
                                    {value: result['free_mem'], name: "空闲内存"},
                                    {value: result['cache/buffer_mem'], name: "缓存"}
                                ]
                            }
                        ]
                    })
                }
            }
        });
}
function disk(node) {
    var node_disk = echarts.init(document.getElementById('node-disk'));
    var cluster_id = window.location.host.split(':')[0];
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id, 'node': node}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/node/disk/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    result = resful['message']['message'];
                    node_disk.hideLoading();
                    node_disk.setOption({
                        title: {
                            text: '硬盘占比',
                            left: 'center'
                        },
                        legend: {
                            data: ['已用储存', "可用储存"],
                            // orient: 'vertical',
                            // y: 'center',    //延Y轴居中
                            // x: 'center' //居右显示
                            bottom: 'top'
                        },
                        toolbox: {
                            show: true,
                            feature: {
                                dataView: {readOnly: false},
                                saveAsImage: {}
                            }
                        },
                        series: [
                            {
                                name: '节点储存',
                                type: 'pie',
                                center: ['50%', '50%'],
                                radius: ['70%', '50%'],
                                // animation: false,
                                label:{            //饼图图形上的文本标签
                                    normal:{
                                        show:true,
                                        textStyle : {
                                            fontWeight : 300 ,
                                            fontSize : 16    //文字的字体大小
                                        },
                                        formatter:'{d}%'
                                    }
                                },
                                data: [
                                    {value: result['used'], name: "已用储存"},
                                    {value: result['available'], name: "可用储存"}
                                ]

                            }
                        ]
                    })
                }
            }
        });
}

function container(node) {
    var node_container = echarts.init(document.getElementById('node-container'));
    var cluster_id = window.location.host.split(':')[0];
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id, 'node': node}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/node/container/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    var result = resful['message'];
                    node_container.hideLoading();
                    node_container.setOption({
                        title: {
                            text: '容器占比',
                            left: 'center'
                        },
                        legend: {
                            data: ['created', "exited", 'paused', 'restart', 'running'],
                            // orient: 'vertical',
                            // y: 'center',    //延Y轴居中
                            // x: 'center' //居右显示
                            bottom: 'top'
                        },
                        toolbox: {
                            show: true,
                            feature: {
                                dataView: {readOnly: false},
                                saveAsImage: {}
                            }
                        },
                        series: [
                            {
                                name: '容器状态',
                                type: 'pie',
                                radius: '65%',
                                center: ['50%', '50%'],
                                roseType: 'angle',
                                // animation: false,
                                label:{            //饼图图形上的文本标签
                                    normal:{
                                        show:true,
                                        textStyle : {
                                            fontWeight : 300 ,
                                            fontSize : 16    //文字的字体大小
                                        },
                                        formatter:'{d}%'
                                    }
                                },
                                data: [
                                    {value: result['created'], name: "created"},
                                    {value: result['exited'], name: "exited"},
                                    {value: result['paused'], name: "paused"},
                                    {value: result['restarting'], name: "restart"},
                                    {value: result['running'], name: "running"}
                                ]

                            }
                        ]
                    })
                }
            }
        });
}


// function init_form(image_server_node) {
//     $.ajax({
//             data: JSON.stringify({'cluster_id': cluster_id, 'image_server': image_server_node}),
//             dataType: 'json',
//             type: 'POST',
//             contentType: 'application/json; charset=UTF-8',
//             url: '/apis/node/image_server/',
//             sync: true,
//             success: function (resful, status) {
//                 if(status && resful['status']) {
//                     $('#node-image-server-info').DataTable({
//                         data: resful['message']['message'],
//                         autoWidth: true,
//                         columns: [
//                             { data: null },
//                             { data: 'short_id' },
//                             { data: 'tag' },
//                             { data: 'size' },
//                             { data: 'created' },
//                             { data: 'os' }
//                         ],
//                         columnDefs: [{
//                             targets: 0,
//                             render: function (data, type, row, meta) {
//                                 var tag = row['tag'];
//                                 var to_host = getQueryVariable('node');
//                                 var image_server = get_select_node();
//                                 return '<button value=\"' + tag + '\" onclick=\"download(\'' + to_host +'\',\''+ tag + '\', \'' + image_server + '\')\" class=\"btn btn-default dropdown-toggle btn-xs\"><i class=\"fa fa-wrench\"></i></button>'
//                             }
//                         },
//                             {orderable: false, targets: 0}
//                         ]
//                     })
//                 }
//             }
//         });
// }
// function init_form(image_server_node) {
//     $.ajax({
//             data: JSON.stringify({'cluster_id': cluster_id, 'image_server': image_server_node}),
//             dataType: 'json',
//             type: 'POST',
//             contentType: 'application/json; charset=UTF-8',
//             url: '/apis/node/image_server_registry/',
//             sync: true,
//             success: function (resful, status) {
//                 if(status && resful['status']) {
//                     $('#node-image-server-info').DataTable({
//                         data: resful['message']['message'],
//                         autoWidth: true,
//                         columns: [
//                             { data: 'repository' },
//                             { data: 'tag' },
//                             { data: null }
//                         ],
//                         columnDefs: [{
//                             targets: 2,
//                             render: function (data, type, row, meta) {
//                                 var repository = row['repository'] + ':' + row['tag'];
//                                 var to_host = getQueryVariable('node');
//                                 var image_server = get_select_node();
//                                 return '<button value=\"' + repository + '\" onclick=\"download(\'' + to_host +'\',\''+ repository + '\', \'' + image_server + '\')\" class=\"btn btn-default dropdown-toggle btn-xs\"><i class=\"fa fa-arrow-down\"></i></button>'
//                             }
//                         },
//                             {orderable: false, targets: 2}
//                         ]
//                     })
//                 }
//                 else {
//                     toastr.error(resful['message']);
//                 }
//             }
//         });
// }
//切换显示备注信息，显示部分或者全部
function changeShowRemarks(obj){    //obj是td -> a
    var obj_parent = $(obj).parent();
    var content = $(obj_parent).attr("content");
    if(content !== null && content !== ''){
        if($(obj_parent).attr("isDetail") === 'true'){//当前显示的是详细备注，切换到显示部分
            //$(obj).removeAttr('isDetail');//remove也可以
            $(obj_parent).attr('isDetail',false);
            $(obj_parent).html(getPartialRemarksHtml(content));
        }else{//当前显示的是部分备注信息，切换到显示全部
            $(obj_parent).attr('isDetail',true);
            $(obj_parent).html(getTotalRemarksHtml(content));
        }
    }
}

//部分备注信息
function getPartialRemarksHtml(remarks){
    return remarks.substr(0,10) + '...&nbsp;&nbsp;<a href="javascript:void(0);" onclick="changeShowRemarks(this)"><b>more</b></a>';
}

//全部备注信息
function getTotalRemarksHtml(remarks){
    return remarks + '&nbsp;&nbsp;<a href="javascript:void(0);" onclick="changeShowRemarks(this)"><b>close</b></a>';
}
// harbor 方式
function init_form(image_server_node) {
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id, 'image_server': image_server_node}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/node/image_harbor_registry/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    $('#node-image-server-info').DataTable({
                        data: resful['message']['message'],
                        autoWidth: true,
                        columns: [
                            { data: 'name' },
                            { data: 'pull_count' },
                            { data: 'star_count' },
                            { data: 'update_time' },
                            { data: 'description' },
                            { data: null }
                        ],
                        columnDefs: [{
                            targets: 5,
                            render: function (data, type, row, meta) {
                                var repository = row['name'];
                                var to_host = getQueryVariable('node');
                                var image_server = get_select_node();
                                return '<button value=\"' + repository + '\" onclick=\"download(\'' + to_host +'\',\''+ repository + '\', \'' + image_server + '\')\" class=\"btn btn-default dropdown-toggle btn-xs\"><i class=\"fa fa-arrow-down\"></i></button>'
                            }
                        },
                            {
                                targets: 4,
                                type: "date",
                                render: function (data, type, row, meta) {
                                    if(data.length > maxLength) {
                                        return getPartialRemarksHtml(data);
                                    }
                                    else {
                                        return data;
                                    }
                                }
                            },
                            {orderable: false, targets: 2}
                        ],
                        createdRow: function (row, data, dataIndex) {
                            if(data['description'].length > maxLength) {
                                $(row).children('td').eq(3).children('a').attr('onclick', 'changeShowRemarks(this)');
                            }
                            $(row).children('td').eq(3).attr('content', data['description'])
                        }
                    })
                }
                else {
                    toastr.error(resful['message']);
                }
            }
        });
}

function get_select_node() {
    var select = document.getElementsByName('select_node');
    var select_node = null;
    for(var j=0; j<select.length; j++) {
        if(select[j].selected) {
            select_node = select[j].value;
        }
    }
    return select_node;
}

function download(to_host, image_name, image_server) {
    $.ajax({
        data: JSON.stringify({'to_host': to_host, 'image_server': image_server, 'image_name': image_name, 'cluster_id': cluster_id}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/node/download/',
        sync: false,
        success: function (resful, status) {
            if(status && resful['status']) {
                toastr.info(resful['message']['message'])
                mk_form(cluster_id);
            }
            else
                toastr.error(resful['message']['message'])
        }
    })
}

function mk_form(cluster_id) {
    if ($('#node-image-server-info').hasClass('dataTable'))
    {
        var dttable = $('#node-image-server-info').dataTable();
        dttable.fnClearTable(); //清空一下table
        dttable.fnDestroy(); //还原初始化了的datatable
    }
    init_form(cluster_id);
}

$(document).ready(function () {
    var node_name = getQueryVariable('node');
    if(!node_name) {
        toastr.error('链接参数异常,' + time + 's后自动跳转到主页');
        setTimeout(ChangeTime, 1000);
    }
    Mem(node_name);
    disk(node_name);
    container(node_name);
    setInterval(function () {
        Mem(node_name);
        disk(node_name);
        container(node_name);
    }, 10000);
    get_image_server();
});