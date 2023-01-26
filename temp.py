from BPTK_Py import Model
from BPTK_Py import sd_functions as sd
import random
model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
                        name='setup_func_mat')
mat1 = model.constant("mat1")
mat1.setup_vector(4, [1, 2, 3, 4])

mat2 = model.constant("mat2")
mat2.setup_vector(4, [-1, 1, 3, 5])

mat3 = model.constant("mat3")
mat3.setup_vector(4, [-1, 1, 3, 5])

test = model.converter("test")

test.equation = sd.min(mat1+mat3, mat2)
data = test.plot(return_df=True)
print(data)
# print(test._elements.matrix_size())

# elements1 = []
# elements2 = []


# def get_random(t):
#     if t == 2:
#         return float(random.randrange(1, 2000) * .1)
#     num = float(random.randrange(-2000, 2000) * .1)
#     while(num == 0.0):
#         num = float(random.randrange(-2000, 2000) * .1)
#     return num

# def setup_matrix(element, i, elements, n):
#     if(n == 1):
#         if isinstance(elements, (float, int)):
#             names = {}
#             for j in range(i[0]):
#                 cur = {}
#                 for x in range(i[1]):
#                     cur[str(x)] = elements
#                 names[str(j)] = cur
#             element.setup_named_matrix(names)
#         else:
#             names = {}
#             for j in range(i[0]):
#                 cur = {}
#                 for x in range(i[1]):
#                     cur[str(x)] = elements[j][x]
#                 names[str(j)] = cur
#             element.setup_named_matrix(names)
#     else:
#         element.setup_matrix(i, elements)


# for n in range(2):
#     for i in range(1, 10):
#         for k in range(1, 10):
#             elements1 = []
#             elements2 = []
#             for temp1 in range(i):
#                 elements1.append([])
#                 elements2.append([])
#                 for temp2 in range(k):
#                     elements1[temp1].append(get_random(0))
#                     elements2[temp1].append(get_random(0))
#             index = str(i) + "_" + str(k) + "_" + str(n)
#             model = Model(starttime=0.0, stoptime=2.0, dt=1.0,
#                         name='setup_func_mat_' + str(i) + "_" + str(k))
        
            
#             test_element2 = model.converter("test_element_element_wise2" + index)
#             setup_matrix(test_element2, [i, k], elements2, n)
#             for j in range(1, i + 1):
#                 for x in range(1, k + 1):
#                     test_element4 = model.constant(
#                         "test_element4_exc_" + str(j) + "_" + str(x) + index)
#                     setup_matrix(test_element4, [j, x], 2.0, n)
#                     # try:
#                     if(x == i):
#                         print(test_element2._elements.matrix_size())
#                         print(test_element4._elements.matrix_size())

#                         test_element3 = model.constant("test_element_exc" + str(j) + "_" + str(x) + index)
#                         test_element3.equation = test_element4.dot(test_element2)
                    #     assert(x == i)
                    # except:
                    #     print(str(n) + " " + str(i) + " " + str(k) + " " + str(j) + " " + str(x))
                    #     print()
                    #     assert(x != i or n == 1)
