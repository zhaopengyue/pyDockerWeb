var maxLength = 20;

function make_action(node, container_id) {
    var set_html = '<div class="btn-group">\n' +
        '<button href="#" class="btn btn-default dropdown-toggle btn-xs" data-toggle="dropdown" role="button" aria-expanded="false"><i class="fa fa-wrench"></i></button>\n' +
        '<ul class="dropdown-menu" role="menu">\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'restart\',' + '{}' + ')"><i class="fa fa-rotate-right">&nbsp;&nbsp;&nbsp;&nbsp;</i>重启</a>\n' +
        '</li>\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'start\',' + '{}' + ')"><i class="fa fa-play">&nbsp;&nbsp;&nbsp;&nbsp;</i>开始</a>\n' +
        '</li>\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'stop\',' + '{}' + ')"><i class="fa fa-stop">&nbsp;&nbsp;&nbsp;&nbsp;</i>停止</a>\n' +
        '</li>\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'pause\',' + '{}' + ')"><i class="fa fa-pause">&nbsp;&nbsp;&nbsp;&nbsp;</i>暂停</a>\n' +
        '</li>\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'unpause\',' + '{}' + ')"><i class="fa fa-dot-circle-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>启动</a>\n' +
        '</li>\n' +
        '<li><a onclick="remove(' + '\'' + node + '\',' + '\'' + container_id + '\'' + ')"><i class="fa fa-scissors">&nbsp;&nbsp;&nbsp;&nbsp;</i>删除</a>\n' +
        '</li>\n' +
        '<li><a onclick="rename(' + '\'' + node + '\',' + '\'' + container_id + '\'' + ')"><i class="fa fa-edit">&nbsp;&nbsp;&nbsp;&nbsp;</i>重命名</a>\n' +
        '</li>\n' +
        // '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'commit\',' + '{}' + ')"><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '<li><a><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '</li>\n' +
        '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'logs\',' + '{}' + ')"><i class="fa fa-file-text-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>日志</a>\n' +
        '</li>\n' +
        '</ul>\n' +
        '</div>';
    return set_html;
}
// 更新节点选择下拉框
function modal_node() {
    var cluster_id = window.location.host.split(':')[0];
    document.getElementById('modal-create-select').innerHTML = '';
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
                        var option = document.createElement('option');
                        option.setAttribute('value', resful['message'][i]['name']);
                        option.setAttribute('name', 'modal-create-option');
                        option.innerText = resful['message'][i]['name'];
                        $("#modal-create-select").append(option);
                    }
                    // $("#modal-create-select").selectpicker('refresh');
                }
                else {
                    toastr.error(resful['message']);
                }
            }
        });
}

function rename(node, container_id) {
    $("#container-new-name").val('');
    $("#modal-rename").modal();
    $("#container-rename-submit").attr('onclick', 'action(\'' + node + '\', \'' + container_id + '\', \'rename\', {})')
}

function remove(node, container_id) {
    $("#modal-remove").modal();
    $("#container-remove-normal").attr('onclick', 'action(\'' + node + '\', \'' + container_id + '\', \'remove\', {})');
    $("#container-remove-force").attr('onclick', 'action(\'' + node + '\', \'' + container_id + '\', \'remove\', {\'force\': true})');
}
function create() {
    modal_node();
    $("#modal-create-select").val('');
    $("#modal-create").modal();
}

// 提交创建命令
function create_submit() {
    var cluster_id = window.location.host.split(':')[0];
    var cmd = $("#txt_cmd").val();
    var total_cmd = 'docker create ' + cmd
    var node_info = $("#modal-create-select option:selected").val();
    $("#modal-create").modal('hide');
    $.ajax({
        data: JSON.stringify({'cluster_id': cluster_id, 'node': node_info, 'cmd': total_cmd}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/container/create/',
        sync: true,
        success: function (resful, status) {
            if(status && resful['status']) {
                toastr.info('创建成功');
                toastr.info('容器ID: \n' + resful['message']);
                mk_form(cluster_id);
            }
            else {
                toastr.error(resful['message']);
                mk_form(cluster_id);
            }
        }
    });
}

function action(node, container_id, action, args) {
    var cluster_id = window.location.host.split(':')[0];
    if(action === 'rename') {
        var new_name = $("#container-new-name").val();
        if(new_name.length === 0) {
            return;
        }
        args = {"new_name": new_name};
    }
    if(action==='remove')
        $("#modal-remove").modal('hide');
    if(action==='rename')
        $("#modal-rename").modal('hide');
    $.ajax({
        data: JSON.stringify({'cluster_id': cluster_id, 'node': node, 'container_id': container_id,'action': action, 'args': args}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/container/operator/',
        sync: true,
        success: function (resful, status) {
            if(status && resful['status']) {
                toastr.info(resful['message']);
                mk_form(cluster_id);
            }
            else {
                toastr.error(resful['message']);
                mk_form(cluster_id);
            }
        }
    });
}

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

function init_form(cluster_id) {
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/container/info/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    $('#container-node-info').DataTable({
                        data: resful['message'],
                        // autoWidth: true,
                        columns: [
                            { data: null },
                            { data: 'short_id' },
                            { data: 'node' },
                            { data: 'name' },
                            { data: 'image' },
                            { data: 'exit_time' },
                            { data: 'create' },
                            { data: 'status' }
                        ],
                          scrollY: "1000px",
                        scrollCollapse: true,
                        paging: true,
                        retrieve:true,
                        columnDefs: [{
                                targets: 0,
                                render: function (data, type, row, meta) {
                                    return make_action(row['node'], row['short_id']);
                                }
                            },
                            {
                                targets: 4,
                                type: "date",
                                render: function (data, type, row, meta) {
                                    if(row['image'].length > maxLength) {
                                        return getPartialRemarksHtml(row['image']);
                                    }
                                    else {
                                        return row['image'];
                                    }
                                }
                            },
                            {
                                targets: 6,
                                type: "date",
                                render: function (data, type, row, meta) {
                                    return data.substr(0, 19);
                                }
                            },
                            {orderable: false, targets: 0}
                        ],
                        createdRow: function (row, data, dataIndex) {
                            if(data['image'].length > maxLength) {
                                $(row).children('td').eq(4).children('a').attr('onclick', 'changeShowRemarks(this)');
                            }
                            $(row).children('td').eq(4).attr('content', data['image'])
                        }
                    })
                }
            }
        });
}

function mk_form(cluster_id) {
    if ($("#container-node-info").hasClass('dataTable'))
    {
        var dttable = $('#container-node-info').dataTable();
        dttable.fnClearTable(); //清空一下table
        dttable.fnDestroy(); //还原初始化了的datatable
    }
    init_form(cluster_id);
}
$(document).ready(function () {
    var cluster_id = window.location.host.split(':')[0];
    init_form(cluster_id);
});