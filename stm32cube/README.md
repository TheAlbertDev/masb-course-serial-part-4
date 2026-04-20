# Serial Communication - Part IV

<img align="left" src="https://img.shields.io/badge/Development Environment-STM32Cube-blue"><img align="left" src="https://img.shields.io/badge/Estimated Duration-2 h-green"><br>

We have already seen what I2C is and how to operate with it using the `Wire` library. Now we will see how to do the same with STM32Cube. Differences? Apart from using the _blocking_ or _polling_ mode, we will also use interrupts to manage I2C communication and free up the CPU. In this part of the practice, we will not detail aspects of the BMP280's operation that we have already seen in the first part (enabling different measurements, compensation formulas, putting the sensor in "Normal" mode, etc.), nor how to manipulate bytes to combine or shift them (which is done exactly the same as in Arduino since it is a feature of the language). If you have doubts or don't remember something, don't hesitate to take a quick look at the previous part. Let's get to it!

## Objectives

- I2C communication using the STM32F4 HAL in _blocking_ mode.
- I2C communication using the STM32F4 HAL with interrupts.

## Procedure

### _Blocking_ Mode

_Blocking_ mode is the same as _polling._ (What is _polling_? Practice 1, please... 🥲) That is, it performs a write or read operation through the I2C bus and waits until the operation is complete. This is what we did in Arduino. We will do the same in STM32Cube. We will do it to read the ID of the BMP280 sensor and check that everything is properly connected. Once this is done, we will see how to operate I2C with interrupts.

![](/.github/images/69ff3d.jpeg)

#### Project Creation and Configuration

First of all, start from the `main` branch, create a branch named `stm32cube/<username>/bmp280`, and create a project named `bmp280` (create it inside the folder named after your username within the workspace). We go to the graphical configuration tool STM32CubeMX and go to the I2C1 tab within _Connectivity_.

> [!NOTE]
> In a microcontroller, it is very common to have more than one repeated module/peripheral. This is the case with I2C, of which there are two. We will work with number 1.

We enable I2C by selecting I2C in the dropdown, and in this case, there is no need to modify anything else. Some important parameters that we could modify are the clock operation frequency (SCL) or the microcontroller's address as a slave. But since we don't need the program to run super fast nor will we operate the microcontroller in slave mode (remember, in this practice the microcontroller is the master), we will not modify the frequency or the address. The datasheets of the sensors/components always indicate the range of frequencies at which they can operate.

The I2C configuration would look like this. Notice how the PB7 and PB6 pins are automatically configured as SDA and SCL.

![](/.github/images/stm32cube-bmp280.png)

**That's wrong!** Peripherals can also be routed through different pins. The default pins chosen by the configuration tool are wrong, and we must indicate the PB9 and PB8 pins as SDA and SCL, respectively.

We will send messages to the serial terminal, so enable/configure the UART for that.

Save and generate the code.

I don't know if it is strictly necessary at this point in the course, but since this is the last practice, I will spell it out anyway: create the `app.c` and `app.h` files, and organize the code using the `setup` and `loop` functions.

#### Requesting the ID

Let's see if everything is properly connected by asking the sensor for its ID, just as we did in Arduino. Remember that this is requesting the content of register `0xD0` and it should return `0x58`. We will do this in the `setup` function.

```c
#include "main.h"
#include <stdio.h>

#define BMP280_ADDRESS 0x76
#define BMP280_REG_ID 0xD0

extern I2C_HandleTypeDef hi2c1;
extern UART_HandleTypeDef huart2;

static uint8_t I2C_TxBuffer[32] = {0}, I2C_RxBuffer[32] = {0};
static uint8_t UART_TxBuffer[64] = {0}, UART_RxBuffer[64] = {0};

void setup(void) {
  I2C_TxBuffer[0] = BMP280_REG_ID;
  HAL_I2C_Master_Transmit(&hi2c1, BMP280_ADDRESS << 1, I2C_TxBuffer, 1, 100);
  HAL_I2C_Master_Receive(&hi2c1, BMP280_ADDRESS << 1, I2C_RxBuffer, 1, 100);

  uint16_t UART_TxBufferElements = 0;

  if (I2C_RxBuffer[0] == 0x58) {
    UART_TxBufferElements = sprintf(UART_TxBuffer, "BMP280 connected!");
  } else {
    UART_TxBufferElements = sprintf(UART_TxBuffer, "No BMP280 found...");
  }
  HAL_UART_Transmit(&huart2, UART_TxBuffer, UART_TxBufferElements, 100);
}

void loop(void) {}
```

Differences from Arduino. As with other peripherals, when using the HAL, we must first indicate the pointer to the structure that contains the peripheral's configuration (in this case, `hi2c1`). Then we pass the slave address, but notice that we shift the bits one position to the left. Why? Remember that the 7 most significant bits of the first byte are the slave address, and the least significant bit indicates whether the operation is read or write. In Arduino, this shift was done behind the scenes by the Wire library. Here we have to do it ourselves. The read/write operation bit is automatically set.

> [!NOTE]
> We can also store the value `0xEC` directly in the `BMP280_ADDRESS` macro, which corresponds to the value `0x76` shifted one bit to the left. But we have done it this way to make it clear that we need to do the shift ourselves.

We also indicate the number of bytes to transmit (in Arduino, we made a separate write instruction for each byte). And finally, we indicate a _timeout_. That is, if the operation is not completed within that time, the instruction is skipped. We didn't do this in Arduino, and if there was a communication failure due to the sensor not being connected or any other reason, the program would get stuck in those _while loops_ we had in the code.

If everything is correct, we run the code, and we should see "BMP280 connected!" in CoolTerm.

In this small example, the instructions halt the code execution until the read/write operation takes place or until the specified _timeout_ time has elapsed. Unacceptable. Let's see how to do it with interrupts so that the CPU can do other more important things.

### Interrupt Mode

The first thing we will do is go to the STM32CubeMX and enable the I2C1 event interrupt from the NVIC Settings tab.

Save and generate the code.

We go to the `app.c` file and add the interrupt _callback_ function.

```c
...

void HAL_I2C_MasterRxCpltCallback (I2C_HandleTypeDef * hi2c) {

	uint16_t UART_TxBufferElements = 0;

	if (I2C_RxBuffer[0] == 0x58) {
		UART_TxBufferElements = sprintf(UART_TxBuffer, "BMP280 connected!");
	} else {
		UART_TxBufferElements = sprintf(UART_TxBuffer, "No BMP280 found...");
	}
	HAL_UART_Transmit(&huart2, UART_TxBuffer, UART_TxBufferElements, 100);

}
```

There are many _callbacks_ for I2C. In this case, we use the _callback_ to handle the interrupt that occurs when the bytes we requested through I2C are received. Now in the `setup` function, we would only have:

```c
...

void setup(void) {
  I2C_TxBuffer[0] = BMP280_REG_ID;
  HAL_I2C_Master_Transmit(&hi2c1, BMP280_ADDRESS << 1, I2C_TxBuffer, 1, 100);
  HAL_I2C_Master_Receive_IT(&hi2c1, BMP280_ADDRESS << 1, I2C_RxBuffer, 1);
}

...
```

We check that it works and... ta-da! We have interrupts working. _Easy peasy lemon squeezy!_

Question for extra credit... Did you notice that we are still doing the transmission without interrupts? Can you imagine why? I'll tell you. If we make both operations with interrupts, as we have the code now, the transmission would start, and without giving it time to finish, we would immediately start the reception. We would be overwriting the write operation, or the read operation would not take place at all. Therefore, we do the write operation in _blocking_ mode so that the code waits for the transmission to be completed, and once done, we start the reception. We do this here to avoid complicating the project with additional code, but write and read operations with interrupts can coexist without problems, and we would simply need to add code to check that the transmission has been completed before performing a reception.

> [!TIP]
> We also have the `HAL_I2C_Mem_Write` and `HAL_I2C_Mem_Read` functions, along with their interrupt-based versions (`*_IT`), which perform both operations we just saw in a single function call. I'll leave it as homework for you to look them up!

## Challenge

This is the end of the guided part... You see it coming, right...? Well, yes. You have to do the previous part (activate the sensor, enable measurements, and obtain temperature and pressure readings), but in STM32Cube. Something important: I don't want you to hate me, so **do it with _blocking_ functions** (without interrupts). This way, the migration from Arduino to STM32Cube is almost direct (if you are a bit "clever," it takes, **literally**, 5 minutes...).

Do not create any new branch or project. Implement the challenge in the project we already have (`bmp280`).

When printing the temperature and atmospheric pressure to the terminal, use the same text format as in the Arduino challenge.

Create a Pull Request from the `stm32cube/<username>/bmp280` branch to `main` and wait for the test results. Correct any undesired behavior detected by the tests, and, once all tests have passed, proceed to merge the Pull Request 🚀

## Evaluation

### Deliverables

These are the elements that should be available to the faculty for your evaluation.

- [ ] **Commits**
      Your remote GitHub repository must contain at least the following required commits: bmp280.

- [ ] **Challenge**
      The challenge must be solved and included with its own commit.

- [ ] **Pull Requests**
      The different Pull Requests requested throughout the practice must also be present in your repository.

## Conclusions

We have now seen how to use I2C in STM32Cube. I2C is the same in both Arduino and STM32Cube; the only difference is the STM32 libraries, which require some additional steps to make them work but offer greater flexibility. This enables the implementation of more advanced projects that can operate in low-power modes or high-computation applications.

Let's go; this was the last practice! We have everything to do the project 🥳
