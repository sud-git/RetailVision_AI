"""
GPU Optimizer - GPU acceleration detection and management

Handles:
- GPU availability detection (CUDA, ROCm)
- GPU memory management
- Fallback to CPU
- Performance metrics
"""

import logging
import torch
import numpy as np
from typing import Optional, Dict, Tuple

from .exceptions import GPUNotAvailableException

logger = logging.getLogger(__name__)


class GPUOptimizer:
    """
    Manages GPU acceleration for video frame processing.
    
    Features:
    - Automatic GPU detection
    - GPU memory allocation and management
    - CPU fallback
    - Performance metrics
    """
    
    def __init__(
        self,
        enable_gpu: bool = True,
        device_id: int = 0,
        gpu_memory_fraction: float = 0.5
    ):
        """
        Initialize GPU optimizer.
        
        Args:
            enable_gpu: Enable GPU if available
            device_id: GPU device ID to use
            gpu_memory_fraction: Fraction of GPU memory to allocate (0.1 - 1.0)
        """
        self.enable_gpu = enable_gpu
        self.device_id = device_id
        self.gpu_memory_fraction = gpu_memory_fraction
        
        # Detection results
        self.cuda_available = False
        self.device = torch.device('cpu')
        self.gpu_info: Dict[str, any] = {}
        
        # Memory tracking
        self.allocated_memory_mb = 0
        self.peak_memory_mb = 0
        
        # Perform detection
        self._detect_gpu()
    
    def _detect_gpu(self) -> None:
        """Detect GPU availability and initialize device"""
        
        try:
            if not self.enable_gpu:
                logger.info("GPU acceleration disabled by configuration")
                self.device = torch.device('cpu')
                return
            
            # Check CUDA availability
            if torch.cuda.is_available():
                self.cuda_available = True
                self.device = torch.device(f'cuda:{self.device_id}')
                
                # Get GPU properties
                gpu_name = torch.cuda.get_device_name(self.device_id)
                gpu_capability = torch.cuda.get_device_capability(self.device_id)
                total_memory = torch.cuda.get_device_properties(
                    self.device_id
                ).total_memory / 1024 / 1024  # Convert to MB
                
                self.gpu_info = {
                    'name': gpu_name,
                    'capability': gpu_capability,
                    'total_memory_mb': total_memory,
                    'compute_capability': f"{gpu_capability[0]}.{gpu_capability[1]}",
                    'backend': 'CUDA'
                }
                
                logger.info(
                    f"GPU detected: {gpu_name} "
                    f"(Compute: {gpu_capability[0]}.{gpu_capability[1]}, "
                    f"Memory: {total_memory:.0f}MB)"
                )
                
                # Allocate GPU memory
                self._allocate_gpu_memory()
                
            else:
                logger.warning("GPU requested but CUDA not available, using CPU")
                self.device = torch.device('cpu')
                
        except Exception as e:
            logger.error(f"GPU detection error: {e}, falling back to CPU")
            self.device = torch.device('cpu')
    
    def _allocate_gpu_memory(self) -> None:
        """Allocate GPU memory based on configuration"""
        try:
            if not self.cuda_available:
                return
            
            props = torch.cuda.get_device_properties(self.device_id)
            total_memory = props.total_memory
            allocated = int(total_memory * self.gpu_memory_fraction)
            
            # Set memory fraction if using per-process memory
            torch.cuda.set_per_process_memory_fraction(
                self.gpu_memory_fraction,
                device=self.device_id
            )
            
            self.allocated_memory_mb = allocated / 1024 / 1024
            logger.info(
                f"Allocated {self.allocated_memory_mb:.0f}MB GPU memory "
                f"({self.gpu_memory_fraction*100:.0f}% of total)"
            )
            
        except Exception as e:
            logger.warning(f"Error allocating GPU memory: {e}")
    
    def transfer_to_device(self, data: np.ndarray) -> torch.Tensor:
        """
        Transfer numpy array to GPU/CPU device.
        
        Args:
            data: Numpy array
            
        Returns:
            Torch tensor on device
        """
        try:
            tensor = torch.from_numpy(data).to(self.device)
            
            # Track memory
            if self.cuda_available:
                used = torch.cuda.memory_allocated(self.device_id) / 1024 / 1024
                self.peak_memory_mb = max(self.peak_memory_mb, used)
            
            return tensor
            
        except Exception as e:
            logger.error(f"Error transferring data to device: {e}")
            # Fallback to CPU
            return torch.from_numpy(data).to(torch.device('cpu'))
    
    def transfer_to_cpu(self, tensor: torch.Tensor) -> np.ndarray:
        """
        Transfer torch tensor to CPU numpy array.
        
        Args:
            tensor: Torch tensor
            
        Returns:
            Numpy array on CPU
        """
        try:
            return tensor.detach().cpu().numpy()
        except Exception as e:
            logger.error(f"Error transferring tensor to CPU: {e}")
            return np.array([])
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get current GPU memory statistics"""
        stats = {
            'allocated_mb': self.allocated_memory_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'cuda_available': self.cuda_available,
        }
        
        if self.cuda_available:
            try:
                reserved = torch.cuda.memory_reserved(self.device_id) / 1024 / 1024
                allocated = torch.cuda.memory_allocated(self.device_id) / 1024 / 1024
                
                stats.update({
                    'reserved_mb': reserved,
                    'in_use_mb': allocated,
                    'free_mb': reserved - allocated,
                })
            except Exception as e:
                logger.warning(f"Error getting GPU memory stats: {e}")
        
        return stats
    
    def clear_cache(self) -> None:
        """Clear GPU cache"""
        if self.cuda_available:
            try:
                torch.cuda.empty_cache()
                logger.debug("GPU cache cleared")
            except Exception as e:
                logger.warning(f"Error clearing GPU cache: {e}")
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available and in use"""
        return self.cuda_available and self.device.type == 'cuda'
    
    def get_device_info(self) -> Dict[str, any]:
        """Get device information"""
        info = {
            'device_type': self.device.type,
            'device_index': self.device_id if self.device.type == 'cuda' else None,
            'cuda_available': self.cuda_available,
            'gpu_info': self.gpu_info,
            'memory_stats': self.get_memory_stats(),
        }
        return info
    
    def __repr__(self) -> str:
        if self.cuda_available:
            return (
                f"GPUOptimizer("
                f"{self.gpu_info.get('name', 'Unknown')}, "
                f"{self.allocated_memory_mb:.0f}MB allocated"
                f")"
            )
        else:
            return "GPUOptimizer(CPU Mode)"


# Global GPU optimizer instance (lazy-initialized)
_gpu_optimizer: Optional[GPUOptimizer] = None


def get_gpu_optimizer(
    enable_gpu: bool = True,
    device_id: int = 0,
    gpu_memory_fraction: float = 0.5
) -> GPUOptimizer:
    """
    Get or create global GPU optimizer instance.
    
    Args:
        enable_gpu: Enable GPU if available
        device_id: GPU device ID
        gpu_memory_fraction: GPU memory fraction
        
    Returns:
        GPUOptimizer instance
    """
    global _gpu_optimizer
    
    if _gpu_optimizer is None:
        _gpu_optimizer = GPUOptimizer(
            enable_gpu=enable_gpu,
            device_id=device_id,
            gpu_memory_fraction=gpu_memory_fraction
        )
    
    return _gpu_optimizer


def reset_gpu_optimizer() -> None:
    """Reset global GPU optimizer (for testing)"""
    global _gpu_optimizer
    if _gpu_optimizer is not None:
        _gpu_optimizer.clear_cache()
    _gpu_optimizer = None
