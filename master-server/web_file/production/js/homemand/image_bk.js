function make_action(node, image_id) {
    var set_html = '<span class="dropdown">\n' +
        '<a href="#" class="btn btn-default dropdown-toggle btn-xs" data-toggle="dropdown" role="button" aria-expanded="false"><i class="fa fa-wrench"></i></a>\n' +
        '<ul class="dropdown-menu" role="menu">\n' +
        '<li><a onclick="remove(' + '\'' + node + '\',' + '\'' + image_id + '\'' + ')"><i class="fa fa-scissors">&nbsp;&nbsp;&nbsp;&nbsp;</i>删除</a>\n' +
        '</li>\n' +
        '<li><a onclick="tag(' + '\'' + node + '\',' + '\'' + image_id + '\'' + ')"><i class="fa fa-edit">&nbsp;&nbsp;&nbsp;&nbsp;</i>打标签</a>\n' +
        '</li>\n' +
        // '<li><a onclick="action(' + '\'' + node + '\',' + '\'' + container_id + '\',' + '\'commit\',' + '{}' + ')"><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '<li><a><i class="fa fa-floppy-o">&nbsp;&nbsp;&nbsp;&nbsp;</i>构建</a>\n' +
        // '</li>\n' +
        '</ul>\n' +
        '</span>';
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
                mk_form(cluster_id);
            }
            else {
                toastr.error(resful['message']);
                mk_form(cluster_id);
            }
        }
    });
}
function init_form(cluster_id) {
    $.ajax({
            data: JSON.stringify({'cluster_id': cluster_id}),
            dataType: 'json',
            type: 'POST',
            contentType: 'application/json; charset=UTF-8',
            url: '/apis/image/info/',
            sync: true,
            success: function (resful, status) {
                if(status && resful['status']) {
                    $('#image-node-info').DataTable({
                        data: resful['message'],
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
                            {orderable: false, targets: 0}
                        ]
                    })
                }
            }
        });
}
function mk_form(cluster_id) {
    if ($('#image-node-info').hasClass('dataTable'))
    {
        var dttable = $('#image-node-info').dataTable();
        dttable.fnClearTable(); //清空一下table
        dttable.fnDestroy(); //还原初始化了的datatable
    }
    init_form(cluster_id);
}
$(document).ready(function () {
    var cluster_id = window.location.host.split(':')[0];
    init_form(cluster_id);
});