import os
import cv2
import numpy as np
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple
from threading import Lock

class PDFImageProcessor:
    def __init__(self, pdf_path: str, output_dir: str, 
                 start_page: int = 1, end_page: int = None,
                 target_width: float = 516.6,
                 zoom: float = 3.0):
        self.pdf_path = pdf_path
        self.output_dir = output_dir
        self.start_page = start_page
        self.end_page = end_page
        self.target_width = target_width
        self.zoom = zoom
        self.min_contour_width = 200
        self.min_contour_height = 200
        self.processed_pages = 0
        self.progress_lock = Lock()

    def _create_output_dir(self, page_num: int) -> str:
        """创建输出目录"""
        page_dir = os.path.join(self.output_dir, f'Word_List_{page_num}')
        os.makedirs(page_dir, exist_ok=True)
        return page_dir

    def _process_cuts(self, image: np.ndarray) -> List[np.ndarray]:
        """优化的图像切割处理"""
        width = image.shape[1]
        num_cuts = int(np.ceil(width / self.target_width))
        
        cuts = [image[:, int(i * self.target_width):int(min((i + 1) * self.target_width, width))]
                for i in range(num_cuts - 1)]
        
        last_start = int((num_cuts - 1) * self.target_width)
        if width - last_start >= self.target_width * 0.5:
            cuts.append(image[:, last_start:])
            
        return cuts

    def _process_contours(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """优化的轮廓处理"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_contours = [cv2.boundingRect(c) for c in contours 
                         if cv2.boundingRect(c)[2] > self.min_contour_width 
                         and cv2.boundingRect(c)[3] > self.min_contour_height]
        
        return sorted(valid_contours, key=lambda x: x[1])

    def _update_progress(self) -> None:
        """更新处理进度并在每10页打印一次"""
        with self.progress_lock:
            self.processed_pages += 1
            if self.processed_pages % 10 == 0:
                print(f"已完成 {self.processed_pages} 页处理")

    def _process_page(self, page_num: int, pdf_document) -> None:
        """处理单个页面"""
        try:
            page_dir = self._create_output_dir(page_num)
            page = pdf_document.load_page(page_num)
            
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat)
            image_path = os.path.join(page_dir, f'page_{page_num}.png')
            pix.save(image_path)
            
            image = cv2.imread(image_path)
            if image is None:
                return

            i = 1
            for idx, (x, y, w, h) in enumerate(self._process_contours(image)):
                cropped = image[y:y+h, x:x+w]
                for cut_idx, cut_image in enumerate(self._process_cuts(cropped)):
                    out_path = os.path.join(page_dir, 
                        f'word_list_{page_num}_{idx + 1}_cut_{i}.png')
                    cv2.imwrite(out_path, cut_image)
                    i += 1
            
            self._update_progress()
            
        except Exception as e:
            print(f"处理第 {page_num} 页时发生错误: {str(e)}")
            raise

    def process(self) -> None:
        """主处理函数"""
        print("开始处理PDF文件...")
        with fitz.open(self.pdf_path) as pdf_document:
            end_page = min(self.end_page or pdf_document.page_count, 
                          pdf_document.page_count)
            total_pages = end_page - self.start_page
            print(f"总计需要处理 {total_pages} 页")
            
            with ThreadPoolExecutor() as executor:
                futures = [
                    executor.submit(self._process_page, page_num, pdf_document)
                    for page_num in range(self.start_page, end_page)
                ]
                
                # 等待所有任务完成，同时处理可能的异常
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"处理过程中发生错误: {str(e)}")
                        
        print(f"PDF处理完成，共处理 {self.processed_pages} 页")

def main():
    processor = PDFImageProcessor(
        pdf_path='word/input.pdf',
        output_dir='word/outpt',
        start_page=1,
        end_page=284
    )
    processor.process()

if __name__ == '__main__':
    main()