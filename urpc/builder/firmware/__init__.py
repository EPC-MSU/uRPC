from urpc.builder.firmware.K1921BK01T import build_K1921BK01T
from urpc.builder.firmware.K1921BK01T_UART import build_K1921BK01T_UART
from urpc.builder.firmware.K1986BE92QI import build_K1986BE92QI
from urpc.builder.firmware.K1986BE92QI_UART import build_K1986BE92QI_UART
from urpc.builder.firmware.LM3S5R31 import build_LM3S5R31
from urpc.builder.firmware.STM32F103C6 import build_STM32F103C6
from urpc.builder.firmware.STM32F103C6_UART import build_STM32F103C6_UART
from urpc.builder.firmware.STM32L053C8 import build_STM32L053C8
from urpc.builder.firmware.STM32L053C8_UART import build_STM32L053C8_UART
from urpc.builder.firmware.STM32F429ZI import build_STM32F429ZI
from urpc.builder.firmware.STM32F429ZI_UART import build_STM32F429ZI_UART
from urpc.builder.firmware.TM4C1294KCPDT import build_TM4C1294KCPDT

# This is useless list
# but it is required for avoiding
# flake8 messages about unused modules
_modules_to_be_used_by_parents = [build_K1921BK01T, build_K1921BK01T_UART,
                                  build_K1986BE92QI, build_K1986BE92QI_UART,
                                  build_LM3S5R31, build_TM4C1294KCPDT,
                                  build_STM32F103C6_UART, build_STM32F103C6,
                                  build_STM32L053C8, build_STM32F429ZI_UART,
                                  build_STM32L053C8_UART, build_STM32F429ZI]
