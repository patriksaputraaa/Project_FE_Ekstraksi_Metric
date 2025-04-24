class Motorcycle(name: String, wheels: Int, val type: String) : Vehicle(name, wheels) {
    fun popWheelie() {
        println("Popping wheelie")
    }
}