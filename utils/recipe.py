import os, sys
import copy

class Ingredient():
    def __init__(self, name, qty=None, notation=None):
        self.name     = name
        # используем для случая, когда ингридиент нужен в разных видах
        # например: картошка нужна как в виде пюре, так в виде сваренной
        # массив количеств
        # TODO: если пользователь вводит 1/3
        if qty: self.qty = [float(qty)]
        else: self.qty = []
        # массив систем счисления
        # преобразуем системы счисления к единой
        #   убираем точки
        #   преобразуем ё в е (кто как пишет)
        #   убираем все, что написанно в скобочках
        if notation:
            _notation = notation.replace(".","").replace("ё", "е")
            self.notation = [_notation]
        else: self.notation = []

    def __iter__(self):
        # позиция на которой мы остановились при
        # итерировании по ингридиентам
        self.curr_idx = 0
        return self

    def __next__(self):
        if self.curr_idx < len(self.qty):
            self.curr_idx += 1
            return Ingredient(self.name,
                    self.qty[self.curr_idx - 1],
                    self.notation[self.curr_idx - 1])
        else:
            raise StopIteration

    def __add__(self, other):
        """
        складываем ингридиенты
        если что-то не получается сложить, то
        """
        lhs = copy.deepcopy(self)
        rhs = copy.deepcopy(other)
        # ищем одинаковые нотации у себя и у другого
        # если нашли такие - складываем и заносим в результат
        result     = Ingredient(lhs.name)
        to_process = []
        for i, l_elem in enumerate(zip(lhs.qty, lhs.notation)):
            for j, r_elem in enumerate(zip(rhs.qty, rhs.notation)):
                if l_elem[-1] == r_elem[-1]:    # сравниваем их системы счисления
                    result.qty.append(l_elem[0]+r_elem[0])  # складываем количество
                    result.notation.append(l_elem[-1])
                    lhs.qty.pop(i)
                    lhs.notation.pop(i)
                    rhs.qty.pop(j)
                    rhs.notation.pop(j)
        # проходимся по оставшемся элементам и заносим их как есть
        for l_elem in lhs:
            result.qty.append(l_elem.qty[0])
            result.notation.append(l_elem.notation[0])
        for r_elem in rhs:
            result.qty.append(r_elem.qty[0])
            result.notation.append(r_elem.notation[0])

        return result

    def __str__(self):
        return ", ".join(
                "{} - {} {}".format(self.name, qty, notation)
                for qty, notation in zip(self.qty, self.notation))

class Recipe():
    # TODO: replace raw string with rere
    ingredients_header = "Продукты"
    instructions_header = "Рецепт:"
    portions_header = "Порции:"
    category_header = "Категория:"

    error_file = os.path.join(os.path.abspath("log"), "error.txt")

    # TODO: write log function
    def __init__(self, fn=""):
        self.name = ""
        self.ingredients = []
        self.instructions = []
        self.portions = 0
        self.category = ""

        # проверяем существует ли файл, если не существует, выводим
        # ошибку в поток ошибок и выходим
        if not os.path.exists(fn):
            print("Recipe '%s' was not found" % fn, file=sys.stderr)
            return

        # берем имя без расширения
        basename = os.path.basename(fn)
        self.name = basename[:basename.find(".")]
        # 0 - еще ничего не считали
        # 1 - считали ингридиенты
        # 2 - считали рецепт
        state = 0
        fd = open(fn, 'r')
        # читаем файл построчно
        #   пустая линия - текущая секция законченна
        #   заголовок - начало секции (не обрабатываем)
        #   во всех остальных случаях - это контент
        for line in fd:
            line = line.strip()
            if state < 1:   # читаем ингридиенты
                # если это пустая строчка - текущая секция закончилась
                if line in "":
                    state += 1
                    continue
                # если это не заголовок - добавляем ингредиент
                elif Recipe.ingredients_header not in line:
                    name = line.split(" - ")[0]
                    qty_notation = line.split(" - ")[-1]
                    qty = qty_notation[:qty_notation.find(" ")]
                    notation = qty_notation[qty_notation.find(" ")+1 :]
                    self.ingredients.append(Ingredient(name, qty, notation))
                # если это заголовок - пропускаем
            elif state < 2: # читаем рецепт \ план выполнения
                # если это пустая строчка - текущая секция закончилась
                if line in "":
                    state += 1
                    continue
                # если это не заголовок - добавляем ингредиент
                elif Recipe.instructions_header not in line:
                    self.instructions.append(line[line.find(" ")+1:].strip())
                # если это заголовок - пропускаем
            else:           # читаем доп. инфу
                if Recipe.portions_header in line:
                    self.portions = int(line.split(" ")[-1])
                elif Recipe.category_header in line:
                    self.category = line.split(" ")[-1]
        fd.close()

    def __bool__(self):
        return len(self.ingredients) > 0


    def __repr__(self):
        return "ok __repr__"

    def __str__(self):
        ret = self.name + "\n"
        ret += "Ingredients:\n" + "\n".join(str(i) for i in self.ingredients)
        ret += "\nRecipe:\n" +\
                "\n".join("{}. {}".format(i, rec)
                for i, rec in enumerate(self.instructions, start=1))

        if self.portions: ret += "\nPortions: {}".format(self.portions)
        if self.category: ret += "\nCategory: {}".format(self.category)
        ret += "\n"
        return ret

    pass
