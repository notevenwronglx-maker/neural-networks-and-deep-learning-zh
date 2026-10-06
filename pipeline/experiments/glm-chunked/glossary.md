# 术语表与标题译表（必须逐字采用）

## 一、术语表（首次出现格式：`\emph{中文}（english）`）

| English | 中文 |
|---|---|
| neural network | 神经网络 |
| deep learning | 深度学习 |
| perceptron | 感知机 |
| sigmoid neuron | S 型神经元 |
| sigmoid function | S 型函数 |
| logistic function | 逻辑斯蒂函数 |
| neuron | 神经元 |
| weight | 权重 |
| bias | 偏置 |
| activation | 激活值 |
| activation function | 激活函数 |
| input layer | 输入层 |
| output layer | 输出层 |
| hidden layer | 隐藏层 |
| threshold | 阈值 |
| cost function | 代价函数 |
| loss / objective function | 损失函数 / 目标函数 |
| quadratic cost | 二次代价 |
| cross-entropy | 交叉熵 |
| mean squared error (MSE) | 均方误差 |
| gradient descent | 梯度下降 |
| stochastic gradient descent (SGD) | 随机梯度下降 |
| learning rate | 学习率 |
| epoch | 轮次 |
| mini-batch | 小批量 |
| batch | 批量 |
| online learning | 在线学习 |
| backpropagation | 反向传播 |
| Hadamard product | Hadamard 积 |
| elementwise | 逐元素的 |
| feedforward | 前馈 |
| training data / training set | 训练数据 / 训练集 |
| test data / test set | 测试数据 / 测试集 |
| validation data / validation set | 验证数据 / 验证集 |
| held-out data | 留出数据 |
| generalization | 泛化 |
| overfitting | 过拟合 |
| underfitting | 欠拟合 |
| regularization | 正则化 |
| weight decay | 权重衰减 |
| L2 regularization | L2 正则化 |
| dropout | dropout（不译） |
| normalization | 规范化 |
| hyper-parameters | 超参数 |
| learning schedule | 学习率日程 |
| early stopping | 提前停止 |
| momentum | 动量 |
| vanishing gradient problem | 梯度消失问题 |
| exploding gradient | 梯度爆炸 |
| unstable gradients | 不稳定的梯度 |
| artificial neuron | 人工神经元 |
| artificial intelligence (AI) | 人工智能 |
| universal approximation / universality | 通用近似 / 通用性 |
| convolutional neural network (CNN) | 卷积神经网络 |
| convolutional layer | 卷积层 |
| pooling layer | 池化层 |
| max-pooling | 最大池化 |
| feature map | 特征图 |
| local receptive field | 局部感受野 |
| shared weights | 权重共享 |
| rectified linear unit (ReLU) | 修正线性单元 |
| tanh neuron | tanh 神经元 |
| softmax | softmax（不译） |
| training example | 训练样本 |
| classification accuracy | 分类准确率 |
| supervised learning | 监督学习 |
| unsupervised learning | 无监督学习 |
| Hebbian rule | Hebb 规则 |
| QWERTY | QWERTY 键盘 |
| recurrent neural network | 循环神经网络 |
| long short-term memory (LSTM) | 长短期记忆网络（LSTM） |
| long-term dependency | 长期依赖 |
| momentum-based | 基于动量的 |
| gradient checking | 梯度检查 |
| overfit | 过拟合（动词） |
| warm up | 热身 |
| bit | 比特 |
| carry bit | 进位比特 |
| sum | 和 |
| expert system | 专家系统 |
| second thoughts | 二段思考（按上下文灵活） |
| rate of learning | 学习速度 |
| saturation | 饱和 |
| saturated neuron | 饱和的神经元 |
| initialization | 初始化 |
| Gaussian random variable | 高斯随机变量 |
| standard deviation | 标准差 |
| mean | 均值 |

## 二、章节标题译表（`\sectionTitle` / `\subsectionTitle` 标题必须逐字采用）

| English 标题 | 中文标题 |
|---|---|
| What is a neural network? | 什么是神经网络？ |
| Perceptrons | 感知机 |
| Sigmoid neurons | S 型神经元 |
| The architecture of neural networks | 神经网络的结构 |
| A simple network to classify handwritten digits | 一个识别手写数字的简单网络 |
| Learning with gradient descent | 用梯度下降进行学习 |
| Implementing our network to classify digits | 实现识别数字的网络 |
| Toward deep learning | 迈向深度学习 |
| Warm up: a fast matrix-based approach to computing the output from a neural network | 热身：基于矩阵的神经网络输出快速计算法 |
| The two assumptions we need about the cost function | 对代价函数的两条假设 |
| The Hadamard product, $s \odot t$ | Hadamard 积：$s \odot t$ |
| The four fundamental equations behind backpropagation | 反向传播背后的四个基本方程 |
| Proof of the four fundamental equations (optional) | 四个基本方程的证明（选读） |
| The backpropagation algorithm | 反向传播算法 |
| The code for backpropagation | 反向传播的代码 |
| In what sense is backpropagation a fast algorithm? | 反向传播究竟快在哪里？ |
| Backpropagation: the big picture | 反向传播：整体图景 |
| What this book is about | 本书是关于什么的 |
| On the exercises and problems | 关于练习与习题 |
| Acknowledgements | 致谢 |
| A principle-oriented approach | 基于原理的路线 |
| A hands-on approach | 动手实践的路线 |
| The cross-entropy cost function | 交叉熵代价函数 |
| Introducing the cross-entropy cost function | 交叉熵代价函数入门 |
| Using the cross-entropy to classify MNIST digits | 用交叉熵分类 MNIST 数字 |
| What does the cross-entropy mean? Where does it come from? | 交叉熵是什么意思？从何而来？ |
| Softmax | Softmax |
| Overfitting and regularization | 过拟合与正则化 |
| Regularization | 正则化 |
| Why does regularization help reduce overfitting? | 正则化为何能减轻过拟合？ |
| Other techniques for regularization | 正则化的其他技术 |
| Weight initialization | 权重初始化 |
| Handwriting recognition revisited: the code | 重访手写数字识别：代码 |
| How to choose a neural network's hyper-parameters? | 如何选择神经网络的超参数？ |
| Variations on stochastic gradient descent | 随机梯度下降的变体 |
| Other models of artificial neuron | 人工神经元的其他模型 |
| Other techniques | 其他技术 |
| Two caveats | 两点说明 |
| Universality with one input and one output | 单输入单输出的通用性 |
| Many input variables | 多个输入变量 |
| Extension beyond sigmoid neurons | 超越 S 型神经元 |
| Fixing up the step functions | 修补阶梯函数 |
| Conclusion | 结语 |
| The vanishing gradient problem | 梯度消失问题 |
| What's causing the vanishing gradient problem? Unstable gradients in deep neural nets | 是什么导致了梯度消失？深度神经网络中不稳定的梯度 |
| Unstable gradients in more complex networks | 更复杂网络中不稳定的梯度 |
| Other obstacles to deep learning | 深度学习的其他障碍 |
| Introducing convolutional networks | 卷积网络入门 |
| Convolutional neural networks in practice | 卷积神经网络的实践 |
| The code for our convolutional networks | 卷积网络的代码 |
| Recent progress in image recognition | 图像识别的最新进展 |
| Approaching the state of the art | 逼近最先进水平 |
| Moving towards deep learning | 迈向深度学习 |
| Is there a simple algorithm for intelligence? | 存在智能的简单算法吗？ |
| Appendix: Is there a \emph{simple} algorithm for intelligence? | 附录：存在\emph{简单}的智能算法吗？ |
| On stories in neural networks | 关于神经网络中的故事 |
| My second thoughts | 我的二段思考 |

（注：若遇到译表未列的标题，按指南自行翻译并保持风格一致。）

## 三、exerciseBox 标题固定译法

- Exercise / Exercises → 练习
- Problem / Problems → 习题

## 四、固定译法短语

| English | 中文 |
|---|---|
| handwritten digits | 手写数字 |
| training examples | 训练样本 |
| bit by bit | 逐比特地 |
| free variables | 自由变量（按数学语境） |
| by and large | 总的来说 |
| picture (intuition sense) | 图景 |
| big picture | 整体图景 |
| toy model | 玩具模型 |
| sanity check | 合理性检查 |
| black box | 黑箱 |
