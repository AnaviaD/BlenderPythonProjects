"""
Módulo para buscar colores exactos en imágenes.
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from collections import Counter
from src.utils.logger import logger


class ColorMatcher:
    """
    Busca colores exactos en imágenes y devuelve las posiciones.
    """
    
    def __init__(self):
        self.target_color: Optional[Tuple[int, int, int]] = None
        self.last_captured_color: Optional[Tuple[int, int, int]] = None
        self.last_captured_area: Optional[dict] = None
        self.sample_area_size: Optional[int] = None      # <--- NUEVO
        self.filter_by_size: bool = True                # <--- NUEVO (activado por defecto)
        logger.info("ColorMatcher inicializado")

    def set_target_color(self, color: Tuple[int, int, int], sample_area_size: int = None):
        """
        Establece el color objetivo y guarda el tamaño de muestra.
        """
        self.target_color = color
        self.sample_area_size = sample_area_size
        
        # Calcular distancia de clustering automática
        if sample_area_size:
            self.cluster_distance = max(5, sample_area_size // 2)
            logger.info(f"📏 Distancia de clustering calculada: {self.cluster_distance} px")
        else:
            self.cluster_distance = 15
        
        logger.info(f"🎯 Color objetivo establecido: RGB{color}")


    def merge_close_points(self, points: List[Tuple[int, int]], min_distance: int) -> List[Tuple[int, int]]:
        """
        Fusiona puntos que están EXTREMADAMENTE cerca (para eliminar duplicados).
        """
        if not points or len(points) < 2:
            return points
        
        # Si la distancia mínima es demasiado pequeña, no fusionar nada
        if min_distance < 2:
            return points
        
        import numpy as np
        points_array = np.array(points)
        
        # Usar un umbral MUY estricto para evitar fusionar objetos distintos
        # Solo fusionar si están a menos de 3 píxeles de distancia
        close_threshold = min(3, min_distance // 2)
        
        merged = []
        used = [False] * len(points_array)
        
        for i in range(len(points_array)):
            if used[i]:
                continue
            
            cluster = [points_array[i]]
            used[i] = True
            
            for j in range(i + 1, len(points_array)):
                if used[j]:
                    continue
                
                # Calcular distancia al punto actual
                dist = np.linalg.norm(points_array[j] - points_array[i])
                
                # Solo fusionar si están MUY cerca (umbral estricto)
                if dist < close_threshold:
                    cluster.append(points_array[j])
                    used[j] = True
            
            # Calcular centro del cluster
            if cluster:
                center = np.mean(cluster, axis=0).astype(int)
                merged.append(tuple(center))
            else:
                merged.append(tuple(points_array[i]))
        
        logger.debug(f"🔗 Fusionados {len(points)} puntos en {len(merged)} (umbral: {close_threshold}px)")
        return merged


    def cluster_positions(self, positions: List[Tuple[int, int]], min_distance: int = 10) -> List[Tuple[int, int]]:
        """
        Agrupa posiciones cercanas usando un grid.
        AHORA con tamaño de celda basado en min_distance (más grande = menos grupos)
        """
        if not positions:
            return []
        
        if len(positions) < 3:
            return positions
        
        # --- TAMAÑO DE CELDA MÁS GRANDE PARA MENOS GRUPOS ---
        # Antes: cell_size = max(3, min_distance // 2)
        # Ahora: cell_size = max(5, min_distance)  # Más grande = menos grupos
        cell_size = max(5, min_distance)
        
        logger.info(f"📊 Grid clustering con cell_size={cell_size}")
        
        grid = {}
        for x, y in positions:
            cell_x = x // cell_size
            cell_y = y // cell_size
            key = (cell_x, cell_y)
            if key not in grid:
                grid[key] = []
            grid[key].append((x, y))
        
        clusters = []
        for key, points in grid.items():
            if points:
                sum_x = sum(p[0] for p in points)
                sum_y = sum(p[1] for p in points)
                center_x = sum_x // len(points)
                center_y = sum_y // len(points)
                clusters.append((center_x, center_y))
        
        logger.info(f"📊 Agrupados {len(positions)} píxeles en {len(clusters)} grupos")
        
        return clusters



    
    def get_color_from_area(self, image: np.ndarray, area: dict) -> Optional[Tuple[int, int, int]]:
        """
        Obtiene el color del PÍXEL CENTRAL del área seleccionada.
        IMPORTANTE: image ya es la imagen RECORTADA del área.
        """
        try:
            # area contiene las coordenadas originales, pero NO las usamos para indexar
            # porque image YA ES la región recortada
            x, y = area['left'], area['top']
            w, h = area['width'], area['height']
            
            self.last_captured_area = area
            
            logger.info(f"📐 Área seleccionada: x={x}, y={y}, w={w}, h={h}")
            logger.info(f"📊 Imagen recibida: shape={image.shape}")
            
            # Validar imagen
            if image is None or image.size == 0:
                logger.error("❌ Imagen vacía")
                return None
            
            # Obtener dimensiones de la imagen RECORTADA
            img_h, img_w = image.shape[:2]
            
            # --- USAR COORDENADAS RELATIVAS ---
            # El centro de la imagen recortada
            center_y = img_h // 2
            center_x = img_w // 2
            
            logger.info(f"🎯 Centro de la imagen recortada: ({center_x}, {center_y})")
            
            # Asegurar que el centro esté dentro de la imagen
            if center_y >= img_h or center_x >= img_w:
                logger.error(f"❌ Centro fuera de la imagen: ({center_x}, {center_y}) vs {image.shape}")
                return None
            
            # Obtener el píxel central EXACTO (BGR)
            pixel_bgr = image[center_y, center_x]
            pixel_rgb = (int(pixel_bgr[2]), int(pixel_bgr[1]), int(pixel_bgr[0]))
            
            logger.info(f"🎯 Píxel CENTRAL exacto: RGB{pixel_rgb}")
            logger.info(f"   HEX: #{pixel_rgb[0]:02x}{pixel_rgb[1]:02x}{pixel_rgb[2]:02x}")
            
            # --- GUARDAR IMAGEN DE PRUEBA ---
            test_img = np.full((100, 100, 3), pixel_rgb, dtype=np.uint8)
            test_img_bgr = cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR)
            cv2.imwrite("test_color.png", test_img_bgr)
            logger.info("📸 Imagen de prueba guardada como 'test_color.png'")
            
            # --- ANÁLISIS DEL ÁREA (INFO) ---
            unique_colors = np.unique(image.reshape(-1, 3), axis=0)
            logger.info(f"🎨 Colores únicos en el área: {len(unique_colors)}")
            
            # Mostrar los colores más comunes
            from collections import Counter
            color_counts = Counter([tuple(c) for c in image.reshape(-1, 3)])
            most_common = color_counts.most_common(5)
            logger.info("📊 Colores más comunes en el área:")
            for color_bgr, count in most_common:
                color_rgb = (int(color_bgr[2]), int(color_bgr[1]), int(color_bgr[0]))
                percentage = (count / (img_w * img_h)) * 100
                logger.info(f"   RGB{color_rgb}: {count} píxeles ({percentage:.1f}%)")
            
            # Guardar el color capturado
            self.last_captured_color = pixel_rgb
            
            return pixel_rgb
            
        except Exception as e:
            logger.error(f"❌ Error capturando color: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None



    def find_exact_color(self, image: np.ndarray, max_pixels: int = 50000) -> List[Tuple[int, int]]:
        """
        Busca TODAS las posiciones donde el color coincide EXACTAMENTE.
        Versión rápida con límite de píxeles y clustering simple.
        AHORA devuelve coordenadas en el espacio ORIGINAL de la imagen.
        """
        if self.target_color is None:
            logger.error("❌ Color objetivo no establecido")
            return []
        
        if image is None or image.size == 0:
            logger.error("❌ Imagen vacía")
            return []
        
        # Convertir color objetivo a BGR
        target_bgr = (self.target_color[2], self.target_color[1], self.target_color[0])
        
        logger.info(f"🔍 Buscando color exacto: RGB{self.target_color}")
        
        # Guardar dimensiones ORIGINALES
        original_h, original_w = image.shape[:2]
        logger.info(f"📐 Tamaño original: {original_w}x{original_h}")
        
        # --- REDUCIR IMAGEN SI ES MUY GRANDE ---
        total_pixels = original_h * original_w
        scale_x = 1.0
        scale_y = 1.0
        working_image = image
        
        if total_pixels > max_pixels:
            scale = (max_pixels / total_pixels) ** 0.5
            new_w = max(10, int(original_w * scale))
            new_h = max(10, int(original_h * scale))
            scale_x = original_w / new_w
            scale_y = original_h / new_h
            logger.info(f"📏 Reduciendo imagen de {original_w}x{original_h} a {new_w}x{new_h} para rendimiento")
            logger.info(f"📐 Factor de escala: x={scale_x:.2f}, y={scale_y:.2f}")
            working_image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        
        # --- BUSCAR COINCIDENCIAS ---
        mask = np.all(working_image == target_bgr, axis=2)
        total_matches = np.sum(mask)
        self.last_match_count = total_matches
        logger.info(f"📊 Coincidencias encontradas: {total_matches}")
        
        if total_matches == 0:
            logger.warning("⚠️ No se encontraron coincidencias exactas")
            return []
        
        # --- OBTENER COORDENADAS (en el espacio de working_image) ---
        y_coords, x_coords = np.where(mask)
        result = list(zip(x_coords.tolist(), y_coords.tolist()))
        
        # ============================================================
        # 🔥 FILTRADO POR TAMAÑO + CLUSTERING
        # ============================================================
        if self.filter_by_size and self.sample_area_size is not None:
            # Usar el tamaño de la muestra para el grid
            # Multiplicamos por el factor de escala para que el grid esté en el espacio de working_image
            grid_size = max(3, int(self.sample_area_size / max(scale_x, scale_y)))
            logger.info(f"📏 Usando grid de {grid_size}px para filtrar por tamaño (muestra: {self.sample_area_size}px)")
            
            # Agrupar en celdas del grid
            grid = {}
            for x, y in result:
                cell_x = x // grid_size
                cell_y = y // grid_size
                key = (cell_x, cell_y)
                if key not in grid:
                    grid[key] = []
                grid[key].append((x, y))
            
            # Filtrar por tamaño y calcular centros
            filtered_centers = []
            max_allowed_size = self.sample_area_size * 3  # <--- Límite: 3 veces la muestra
            
            for key, points in grid.items():
                if not points:
                    continue
                
                # Calcular bounding box de los puntos en la celda
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                
                # Tamaño estimado del objeto (diámetro o lado)
                size_x = max_x - min_x + 1
                size_y = max_y - min_y + 1
                obj_size = max(size_x, size_y)
                
                # Si el objeto es demasiado grande, descartarlo
                if obj_size > max_allowed_size:
                    logger.debug(f"🗑️ Descartado objeto de tamaño {obj_size} > {max_allowed_size}")
                    continue
                
                # Calcular centro del cluster (promedio)
                center_x = sum(xs) // len(points)
                center_y = sum(ys) // len(points)
                filtered_centers.append((center_x, center_y))
            
            logger.info(f"📊 {len(filtered_centers)} objetos conservados (de {len(grid)} grupos)")
            clustered = filtered_centers
        
        else:
            # --- CLUSTERING NORMAL (sin filtro de tamaño) ---
            cluster_distance = getattr(self, 'cluster_distance', 10)
            logger.info(f"📊 Agrupando con distancia: {cluster_distance} píxeles")
            
            if len(result) < 10:
                clustered = result
            else:
                clustered = self.cluster_positions(result, cluster_distance)
            
            logger.info(f"📊 {len(clustered)} grupos encontrados (de {len(result)} píxeles)")
        
        # ============================================================
        # 🔥 NUEVO: FILTRO DE DISTANCIA MÍNIMA (EVITA CLICS DUPLICADOS)
        # ============================================================
        # Este filtro fusiona puntos que están demasiado cerca entre sí
        # para evitar múltiples clics en el mismo objetivo
        if clustered:
            if self.sample_area_size is not None:
                # Usar un umbral MUY pequeño para evitar fusionar objetos distintos
                # Solo fusionar duplicados que están a menos de 3-4 píxeles
                min_distance = max(3, int(self.sample_area_size * 0.3))
            else:
                min_distance = 3
            
            logger.info(f"🔗 Fusionando puntos muy cercanos (umbral: {min_distance} px)")
            original_count = len(clustered)
            clustered = self.merge_close_points(clustered, min_distance)
            logger.info(f"📊 {original_count} → {len(clustered)} puntos después de fusión")
        
        # ============================================================
        # ESCALAR COORDENADAS AL TAMAÑO ORIGINAL
        # ============================================================
        if scale_x != 1.0 or scale_y != 1.0:
            logger.info(f"📏 Escalando coordenadas al tamaño original...")
            scaled_positions = []
            for x, y in clustered:
                orig_x = int(x * scale_x)
                orig_y = int(y * scale_y)
                scaled_positions.append((orig_x, orig_y))
            clustered = scaled_positions
            logger.info(f"✅ {len(clustered)} objetivos en coordenadas originales")
        
        return clustered