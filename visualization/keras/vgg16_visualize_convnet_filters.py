import argparse
import sys
import numpy as np

from tensorflow.contrib.keras import applications
from tensorflow.contrib.keras import backend as K

import matplotlib.pyplot as plt

EPSILON = 1e-5


def tensor_to_image(x):
    x -= x.mean()
    x /= (x.std() + EPSILON)
    x *= 0.1  # ensure that std-dev is 0.1

    x += 0.5
    x = np.clip(x, 0, 1)

    x *= 255
    x = np.clip(x, 0, 255).astype(np.uint8)
    return x


def generate_pattern(model, layer_name, filter_index, step_rate, size=224):
    layer_output = model.get_layer(layer_name).output
    loss = K.mean(layer_output[:, :, :, filter_index])

    # obtain the gradient of the loss with respect to the model's input image
    grads_list = K.gradients(loss, model.input)
    grads = grads_list[0]

    # gradient normalization trick
    grads /= (K.sqrt(K.mean(K.square(grads))) + EPSILON)

    # fetch loss and normalized-gradients for a given input
    iterate = K.function(inputs=[model.input], outputs=[loss, grads])

    # loss maximization via stochastic gradient descent
    input_img_data = np.random.random((1, size, size, 3)) * 20 + 128  # start from gray image with random noise
    for i in range(40):
        loss_value, grads_value = iterate([input_img_data])
        # gradient ascent: adjust the input image in the direction that maximizes the loss
        input_img_data += grads_value * step_rate

    img_tensor = input_img_data[0]
    return tensor_to_image(img_tensor)


def main(_):
    model = applications.VGG16(weights='imagenet',
                               include_top=False)

    n = 8
    results = np.zeros((n * FLAGS.size + (n - 1) * FLAGS.margin,
                        n * FLAGS.size + (n - 1) * FLAGS.margin,
                        3), dtype=np.uint8)

    for i in range(n):
        for j in range(n):
            filter_img = generate_pattern(model,
                                          FLAGS.layer_name,
                                          i + (j * n),
                                          FLAGS.step_rate,
                                          FLAGS.size)
            x_start = i * FLAGS.size + i * FLAGS.margin
            x_end = x_start + FLAGS.size
            y_start = j * FLAGS.size + j * FLAGS.margin
            y_end = y_start + FLAGS.size
            results[x_start:x_end, y_start:y_end, :] = filter_img

    print(results.dtype)
    plt.figure(figsize=(20, 20))
    plt.imshow(results)
    plt.show()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--step_rate', type=float, default=1.0,
                        help='The step rate of gradient ascent')
    parser.add_argument('--layer_name', type=str, default='block5_conv1',
                        help='The convolution layer name to visualize')
    parser.add_argument('--size', type=int, default=128,
                        help='The size of filters to show')
    parser.add_argument('--margin', type=int, default=5,
                        help='The margin to use')
    FLAGS, unparsed = parser.parse_known_args()
    main([sys.argv[0]] + unparsed)
