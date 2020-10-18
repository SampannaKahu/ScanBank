# from vendor.tensorboxresnet.tensorboxresnet.utils.slim_nets import inception_v1 as inception
# from vendor.tensorboxresnet.tensorboxresnet.utils.slim_nets import resnet_v1 as resnet
from tf_slim.nets import resnet_v1 as resnet
from tf_slim.nets import inception_v1 as inception

# import tensorflow.contrib.slim as slim
from tf_slim.ops.arg_scope import arg_scope


def model(x, H, reuse, is_training=True):
    if H['slim_basename'] == 'resnet_v1_101':
        with arg_scope(resnet.resnet_arg_scope()):
            _, T = resnet.resnet_v1_101(
                x, is_training=is_training, num_classes=1000, reuse=reuse
            )
    elif H['slim_basename'] == 'InceptionV1':
        with arg_scope(inception.inception_v1_arg_scope()):
            _, T = inception.inception_v1(
                x,
                is_training=is_training,
                num_classes=1001,
                spatial_squeeze=False,
                reuse=reuse
            )
    #print '\n'.join(map(str, [(k, v.op.outputs[0].get_shape()) for k, v in T.iteritems()]))

    coarse_feat = T[H['slim_top_lname']][:, :, :, :H['later_feat_channels']]
    assert coarse_feat.op.outputs[0].get_shape()[3] == H['later_feat_channels']

    # fine feat can be used to reinspect input
    attention_lname = H.get('slim_attention_lname', 'Mixed_3b')
    early_feat = T[attention_lname]

    return coarse_feat, early_feat
