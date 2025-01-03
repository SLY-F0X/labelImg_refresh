import codecs
import os

from libs.constants import DEFAULT_ENCODING

TXT_EXT = '.txt'
ENCODE_METHOD = DEFAULT_ENCODING

class YOLOWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False
        self.class_list = []  # Ensures unique class names

    def add_bnd_box(self, x_min, y_min, x_max, y_max, name, difficult):
        if x_min >= x_max or y_min >= y_max:
            raise ValueError("Invalid bounding box dimensions")
        if name not in self.class_list:
            self.class_list.append(name)
        self.box_list.append({
            'xmin': x_min, 'ymin': y_min, 'xmax': x_max,
            'ymax': y_max, 'name': name, 'difficult': difficult
        })

    def bnd_box_to_yolo_line(self, box, class_list=None):
        if class_list is None:
            class_list = []
        x_min = box['xmin']
        x_max = box['xmax']
        y_min = box['ymin']
        y_max = box['ymax']

        x_center = float((x_min + x_max)) / 2 / self.img_size[1]
        y_center = float((y_min + y_max)) / 2 / self.img_size[0]

        w = float((x_max - x_min)) / self.img_size[1]
        h = float((y_max - y_min)) / self.img_size[0]

        # PR387
        box_name = box['name']
        if box_name not in class_list:
            class_list.append(box_name)

        class_index = class_list.index(box_name)

        return class_index, x_center, y_center, w, h

    def save(self, class_list=None, target_file=None):
        if class_list is None:
            class_list = []
        if target_file is None:
            target_file = self.filename + '.txt'

        class_list = list(set(class_list))  # Ensure class_list has unique values

        if target_file is None:
            out_file = open(
            self.filename + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(self.filename)), "labels.txt")
            out_class_file = open(classes_file, 'w')

        else:
            out_file = codecs.open(target_file, 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(target_file)), "labels.txt")
            out_class_file = open(classes_file, 'w')


        for box in self.box_list:
            class_index, x_center, y_center, w, h = self.bnd_box_to_yolo_line(box, class_list)
            # print (classIndex, x_center, y_center, w, h)
            # print (out_class_file)
            out_file.write("%d %.6f %.6f %.6f %.6f\n" % (class_index, x_center, y_center, w, h))

        # print (classList)
        # print (out_class_file)
        for c in class_list:
            out_class_file.write(c+'\n')

        out_class_file.close()
        out_file.close()

class YoloReader:

    def __init__(self, file_path, image, class_list_path=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.file_path = file_path

        if class_list_path is None:
            dir_path = os.path.dirname(os.path.realpath(self.file_path))
            self.class_list_path = os.path.join(dir_path, "labels.txt")
        else:
            self.class_list_path = class_list_path

        # print (file_path, self.class_list_path)

        classes_file = open(self.class_list_path, 'r')
        self.classes = classes_file.read().strip('\n').split('\n')
        # print (self.classes)

        img_size = [image.height(), image.width(),
                    1 if image.isGrayscale() else 3]

        self.img_size = img_size

        self.verified = False
        try:
            self.parse_yolo_format()
        except Exception as e:
            print(f"Error in labels format {e}")
            return

    def get_shapes(self):
        return self.shapes

    def add_shape(self, label, x_min, y_min, x_max, y_max, difficult):

        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        self.shapes.append((label, points, None, None, difficult))

    def yolo_line_to_shape(self, class_index, x_center, y_center, w, h):
        if int(class_index) >= len(self.classes):
            print(f"Warning: Class index {class_index} is not in the predefined class list {self.classes}. Adding a new class.")
            new_class = f"Class_{class_index}"
            self.classes.append(new_class)  # Добавляем новый класс
            label = new_class
        else:
            label = self.classes[int(class_index)]

        x_min = max(float(x_center) - float(w) / 2, 0)
        x_max = min(float(x_center) + float(w) / 2, 1)
        y_min = max(float(y_center) - float(h) / 2, 0)
        y_max = min(float(y_center) + float(h) / 2, 1)

        x_min = round(self.img_size[1] * x_min)
        x_max = round(self.img_size[1] * x_max)
        y_min = round(self.img_size[0] * y_min)
        y_max = round(self.img_size[0] * y_max)

        return label, x_min, y_min, x_max, y_max

    def parse_yolo_format(self):
        bnd_box_file = open(self.file_path, 'r')
        for bndBox in bnd_box_file:
            # Fix potential format issues with comma instead of period
            if ',' in bndBox:
                print(f"Warning: Detected comma in bounding box data. Converting to period: {bndBox.strip()}")
            bndBox = bndBox.replace(',', '.')
            class_index, x_center, y_center, w, h = bndBox.strip().split(' ')
            label, x_min, y_min, x_max, y_max = self.yolo_line_to_shape(class_index, x_center, y_center, w, h)

            # Caveat: difficult flag is discarded when saved as yolo format.
            self.add_shape(label, x_min, y_min, x_max, y_max, False)
