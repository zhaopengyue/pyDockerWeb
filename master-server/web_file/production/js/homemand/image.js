var maxLength = 30;

function make_action(node, image_id) {
    var set_html = '<div class="dropup">\n' +
        '<button href="#" class="btn btn-default dropdown-toggle btn-xs" data-toggle="dropdown" role="button" aria-expanded="false"><i class="fa fa-wrench"></i></button>\n' +
        '<ul class="dropdown-menu" role="menu">\n' +
        '<li><a onclick="remove(' + '\'' + node + '\',' + '\'' + image_id + '\'' + ')"><i class="fa fa-scissors">&nbsp;&nbsp;&nbsp;&nbsp;</i>删除</a>\n' +
        '</li>\n' +
        '<li><a onclick="tag(' + '\'' + node + '\',' + '\'' + image_id + '\'' + ')"><i class="fa fa-edit">&nbsp;&nbsp;&nbsp;&nbsp;</i>打标签</a>\n' +
        '</li>\n' +
        // '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'commit\',' + '{}' + ')"><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '<li><a><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '</li>\n' +
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
                if(status) {
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
            }
        });
}

function tag(node, image_id) {
    $("#image-new-tag").val('');
    $("#image-new-repository").val('');
    $("#modal-rename").modal();
    $("#image-rename-submit").attr('onclick', 'action(\'' + node + '\', \'' + image_id + '\', \'tag\', {})')
}

function remove(node, image_id) {
    $("#modal-remove").modal();
    $("#image-remove-normal").attr('onclick', 'action(\'' + node + '\', \'' + image_id + '\', \'remove\', {})');
    $("#image-remove-force").attr('onclick', 'action(\'' + node + '\', \'' + image_id + '\', \'remove\', {\'force\': true})');
}

function action(node, image_id, action, args) {
    var cluster_id = window.location.host.split(':')[0];
    if(action === 'tag') {
        var new_repository = $("#image-new-repository").val();
        var new_tag = $("#image-new-tag").val();
        if(new_repository.length === 0) {
            return;
        }
        if(new_tag.length === 0)
            new_tag = null;
        args = {"repository": new_repository, 'tag': new_tag};
    }
    if(action==='remove')
        $("#modal-remove").modal('hide');
    if(action==='tag')
        $("#modal-rename").modal('hide');
    $.ajax({
        data: JSON.stringify({'cluster_id': cluster_id, 'node': node, 'image_id': image_id,'action': action, 'args': args}),
        dataType: 'json',
        type: 'POST',
        contentType: 'application/json; charset=UTF-8',
        url: '/apis/image/operator/',
        sync: true,
        success: function (resful, status) {
            if(status && resful['status']) {
                toastr.info(resful['message']);
                $("#image-node-info").DataTable().ajax.reload();
            }
            else {
                toastr.error(resful['message']);
                $("#image-node-info").DataTable().ajax.reload();
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
    $('#image-node-info').DataTable({
        ajax: {
            url: '/apis/image/info/',
            type: 'POST',
            dataType: 'json',
            dataSrc: function (data) {
                if(data['status']) {
                    return data['message'];
                } else{
                    return [];
                }
            },
            data: function() {
               return JSON.stringify({'cluster_id': cluster_id})
            },
            contentType: 'application/json; charset=UTF-8'
        },
        autoWidth: true,
        columns: [
            { data: null },
            { data: 'short_id' },
            { data: 'node' },
            { data: 'tag' },
            { data: 'size' },
            { data: 'created' },
            { data: 'os' },
            { data: 'status' }
        ],
        columnDefs: [{
                targets: 0,
                render: function (data, type, row, meta) {
                    return make_action(row['node'], row['tag']);
                }
            },
            {
                targets: 3,
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
            {orderable: false, targets: 0}
        ],
        createdRow: function (row, data, dataIndex) {
            if(data['tag'].length > maxLength) {
                $(row).children('td').eq(3).children('a').attr('onclick', 'changeShowRemarks(this)');
            }
            $(row).children('td').eq(3).attr('content', data['tag'])
        }
    })
}
$(document).ready(function () {
    var cluster_id = window.location.host.split(':')[0];
    init_form(cluster_id);
});