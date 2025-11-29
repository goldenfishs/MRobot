#ifndef __LCD_H
#define __LCD_H

/* Includes ----------------------------------------------------------------- */
#include "device/device.h"
#include "bsp/spi.h"
#include "bsp/gpio.h"

/* USER INCLUDE BEGIN */

/* USER INCLUDE END */

/* USER DEFINE BEGIN */

/* USER DEFINE END */

/* Exported constants ------------------------------------------------------- */
/* Exported macro ----------------------------------------------------------- */
/* Exported types ----------------------------------------------------------- */
/******************************************************************************
	  屏幕属性
******************************************************************************/
/* USER ATTRIBUTE BEGIN */
#define LCD_WIDTH  135 
#define LCD_HEIGHT 240 

#define X_OFFSET 52 
#define Y_OFFSET 40 
/* USER ATTRIBUTE END */
/******************************************************************************
      控制引脚
******************************************************************************/
/* USER PIN BEGIN */
#define LCD_CS_LOW()    HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_RESET)
#define LCD_CS_HIGH()   HAL_GPIO_WritePin(LCD_CS_GPIO_Port, LCD_CS_Pin, GPIO_PIN_SET)
#define LCD_DC_LOW()    HAL_GPIO_WritePin(LCD_RS_GPIO_Port, LCD_RS_Pin, GPIO_PIN_RESET)
#define LCD_DC_HIGH()   HAL_GPIO_WritePin(LCD_RS_GPIO_Port, LCD_RS_Pin, GPIO_PIN_SET)
#define LCD_RST_LOW()   HAL_GPIO_WritePin(LCD_RES_GPIO_Port, LCD_RES_Pin, GPIO_PIN_RESET)
#define LCD_RST_HIGH()  HAL_GPIO_WritePin(LCD_RES_GPIO_Port, LCD_RES_Pin, GPIO_PIN_SET)
/* USER PIN END */
/******************************************************************************
      常用颜色(RGB565)
******************************************************************************/
/* USER COLOR BEGIN */
#define ALICEBLUE       0xEFBF  // 爱丽丝蓝
#define ANTIQUEWHITE    0xF75A  // 古董白
#define AQUA            0x07FF  // 水色
#define AQUAMARINE      0x7FFA  // 碧绿色
#define AZURE           0xEFFF  // 天蓝色
#define BEIGE           0xF7BB  // 米色
#define BISQUE          0xFF18  //  Bisque色
#define BLACK           0x0000  // 黑色
#define BLANCHEDALMOND  0xFF59  // 漂白的杏仁色
#define BLUE            0x001F  // 蓝色
#define BROWN           0xA145  // 棕色
#define BURLYWOOD       0xDDB0  // 木色
#define CADETBLUE       0x64F3  // 军校蓝
#define CHARTreuse      0x7FE0  // 鲜绿色
#define CHOCOLATE       0xD344  // 巧克力色
#define CORAL           0xFBEA  // 珊瑚色
#define CORNFLOWERBLUE  0x64BD  // 矢车菊蓝
#define CORNSILK        0xFFBB  // 玉米丝色
#define CRIMSON         0xD8A7  // 深红
#define CYAN            0x07FF  // 青色
#define DARKBLUE        0x0011  // 深蓝色
#define DARKCYAN        0x0451  // 深青色
#define DARKGOLDENROD   0xB421  // 深金菊色
#define DARKGRAY        0xAD55  // 深灰色
#define DARKGREEN       0x0320  // 深绿色
#define DARKGREY        0xAD55  // 深灰色（同DARKGRAY）
#define DARKOLIVEGREEN  0x5346  // 深橄榄绿
#define DARKORANGE      0xFC60  // 深橙色
#define DARKVIOLET      0x901A  // 深紫罗兰色
#define DEEPPINK        0xF8B2  // 深粉红色
#define DEEPSKYBLUE     0x05FF  // 深天蓝色
#define DODGERBLUE      0x249F  // 闪兰色
#define FIREBRICK       0xB104  // 火砖色
#define FUCHSIA         0xF81F  // 紫红色
#define GAINSBORO       0xDEDB  // 增白
#define GOLD            0xFEA0  // 金色
#define GOLDENROD       0xDD24  // 金菊色
#define GRAY            0x8410  // 灰色
#define GREEN           0x0400  // 绿色
#define GREENYELLOW     0xAFE6  // 绿黄色
#define GREY            0x8410  // 灰色（同GRAY）
#define HONEYDEW        0xEFFD  // 蜜色
#define HOTPINK         0xFB56  // 热粉红色
#define IVORY           0xFFFD  // 象牙色
#define KHAKI           0xEF31  // 卡其色
#define LAVENDER        0xE73E  // 淡紫色
#define LIME            0x07E0  // 酸橙绿
#define LIMEGREEN       0x3666  // 酸橙绿
#define LINEN           0xF77C  // 亚麻色
#define MAGENTA         0xF81F  // 洋红色
#define MAROON          0x8000  // 褐红色
#define MEDIUMAQUAMARINE 0x6675 // 中等碧绿色
#define MEDIUMBLUE      0x0019  // 中等蓝色
#define MEDIUMPURPLE    0x939b  // 中等紫色
#define MEDIUMSEAGREEN  0x3d8e  // 中等海绿色
#define MEDIUMSLATEBLUE 0x7b5d  // 中等石板蓝
#define MEDIUMSPRINGGREEN 0x07d3 // 中等春绿色
#define MEDIUMTURQUOISE 0x4e99  // 中等青绿色
#define MEDIUMVIOLETRED 0xC0B0  // 中等紫红色
#define MIDNIGHTBLUE    0x18CE  // 午夜蓝
#define MINTCREAME      0xF7FE  // 薄荷奶油色
#define MISTYROSE       0xFF1B  // 雾玫瑰色
#define MOCCASIN        0xFF16  // 鹿皮色
#define NAVAJOWHITE     0xFEF5  // Navajo白
#define NAVY            0x0010  // 海军蓝
#define OLDLACE         0xFFBC  // 旧蕾丝色
#define OLIVE           0x8400  // 橄榄色
#define OLIVEDRAB       0x6C64  // 橄榄褐色
#define ORANGE          0xFD20  // 橙色
#define ORANGERED       0xFA20  // 橙红色
#define ORCHID          0xDB9A  // 兰花色
#define PALE GOLDENROD  0xEF35  // 苍白金菊色
#define PALEGREEN       0x97D2  // 苍白绿色
#define MEDIUMORCHID    0xbaba  // 中等紫罗兰色
#define VIOLET        	0xEC1D  // 紫罗兰色  /--- *I LOVE VIOLET FOREVER！！T-T* ---/
#define VIOLET_SOFT 	0xE31F  // 柔和的紫罗兰色
/* USER COLOR END */
/******************************************************************************
      end--常用颜色(RGB565)
******************************************************************************/

typedef enum {
    LCD_ORIENTATION_PORTRAIT = 0,  // 竖屏模式
    LCD_ORIENTATION_LANDSCAPE = 1, // 横屏模式（90°顺时针旋转）
    LCD_ORIENTATION_LANDSCAPE_INVERTED = 2, // 横屏模式（90°逆时针旋转）
    LCD_ORIENTATION_PORTRAIT_INVERTED = 3  // 竖屏模式（180°旋转）
} LCD_Orientation_t;

typedef enum {
    LSB=0,
    MSB=1,
}LCD_BitOrder_t;

/* Exported functions prototypes -------------------------------------------- */
int8_t LCD_Init(LCD_Orientation_t orientation);
int8_t LCD_Clear(uint16_t color);

int8_t LCD_DrawPoint(uint16_t x, uint16_t y, uint16_t color);
int8_t LCD_DrawLine(uint16_t x0, uint16_t y0, uint16_t x1, uint16_t y1, uint16_t color);
int8_t LCD_DrawRectangle(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2,uint16_t color);
int8_t LCD_DrawHollowCircle(uint16_t x0,uint16_t y0,uint16_t r,uint16_t color);
int8_t LCD_DrawSolidCircle(uint16_t x0, uint16_t y0, uint16_t r, uint16_t color);
int8_t LCD_DrawChar(uint16_t x, uint16_t y, char ch, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order);
int8_t LCD_DrawString(uint16_t x, uint16_t y, const char *str, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order);
int8_t LCD_DrawInteger(uint16_t x, uint16_t y, int32_t num, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order);
int8_t LCD_DrawFloat(uint16_t x, uint16_t y, float num, uint8_t decimal_places, uint16_t color, uint8_t font_size, LCD_BitOrder_t bit_order);
int8_t LCD_DrawBitmap(const uint8_t *bitmap, uint16_t x, uint16_t y, uint16_t width, uint16_t height, uint16_t color, LCD_BitOrder_t bit_order);

/* USER FUNCTION BEGIN */

/* USER FUNCTION END */
#endif // __LCD_H
