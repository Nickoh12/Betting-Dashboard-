library(shiny)
library(dplyr)
library(tidyverse)
library(shinythemes)
library(ggplot2)
library(shinydashboard)
library(flexdashboard)
library("RMariaDB")
library(glue)
library(plotly)
library(DT)

ui<- fluidPage(
  dashboardHeader(title= "Sports Betting App"),
  dashboardSidebar(sidebarMenu(
     actionButton("update", "Update"),
            radioButtons("model", "Model:",
                         c("Pinnacle Equal Margins", "Pinnacle Proportional Margins",
                           "Consensus Equal Margins", "Consensus Proportional Margins"), 
                         selected= "Pinnacle Equal Margins"))
            #uiOutput('date')
            
      )
               ,
  dashboardBody(
    plotlyOutput('odds'),
    DT::dataTableOutput('matches')
  )
  
)

server<- function(input, output,session){
  
  get_data<- function(table_name){
    mydb = dbConnect(RMariaDB::MariaDB(), user="root",  password="4kS8GdBm!",dbname="betbrain", host="localhost") 
    query= "select * from {table_name}"
    input= glue(query)
    rs= dbSendQuery(mydb, input)
    data= dbFetch(rs,n= -1)
    dbClearResult(rs)
    dbDisconnect(mydb)
    return (data)
  }
  
  zeitachse<- function(start, end,list,breaks){
    if (end-start>=1800){
      end= end-1800
      list= append(list,end)
      return (zeitachse(start,end,list,breaks))
    }
    else{
      list=append(list, start)
    }
    if (breaks== "yes"){
      return (list-7200)
    }
    else if (breaks== "no"){
      return(as.POSIXct(list-7200, origin="1970-01-01", tz= "Europe/Berlin"))
    }
  }
  
  panel_plots<-function(home,away,playtime,testgroup,number){
    
    short= testgroup%>%filter(home_team == home & away_team== away,date==playtime)
    
    if (number == 1 |number== 2){
      names(short)[18]<-'ProbsH'
      names(short)[19]<-'ProbsD'
      names(short)[20]<-'ProbsA'
      names(short)[21]<-'MarginH'
      names(short)[22]<-'MarginD'
      names(short)[23]<-'MarginA'}
    else if (number == 3 |number== 4){
      names(short)[14]<-'ProbsH'
      names(short)[15]<-'ProbsD'
      names(short)[16]<-'ProbsA'
      names(short)[17]<-'MarginH'
      names(short)[18]<-'MarginD'
      names(short)[19]<-'MarginA'
    }
    
    
    short$FairOddsH<-1/short$ProbsH
    short$FairOddsD<-1/short$ProbsD
    short$FairOddsA<-1/short$ProbsA
    
    unixbreaks= zeitachse(min(as.numeric(short$scrape_time)),as.numeric(short$date[1]),
                          c(as.numeric(short$date[1])), 'yes')
    
    timebreaks= zeitachse(min(as.numeric(short$scrape_time)),as.numeric(short$date[1]),
                          c(as.numeric(short$date[1])), 'no')
    
    home_plot<-ggplot(short) +
      geom_line(aes(x=as.numeric(scrape_time)-7200, y=maxOddsH),size= 1, linetype= 'twodash',
                color= 'darkgreen')+
      geom_point(aes(x=as.numeric(scrape_time)-7200, y=maxOddsH,
                     text= paste("Max Bookie: ",substr(maxBookieH,1,nchar(maxBookieH)-1),
                                 "\n Max Odds: ", round(maxOddsH,4),
                                 "\n Fair Odds: ", round(FairOddsH,4),
                                 "\n Margin: ",glue("{round(MarginH*100,2)} %"),
                                 "\n Scrape Time: ", scrape_time
                                 
                     )
      ),size= 3,color= 'darkgreen')+
      geom_line(aes(x= as.numeric(scrape_time)-7200, y= FairOddsH), linetype= 'twodash',
                size= 1,color= 'firebrick')+
      geom_point(aes(x= as.numeric(scrape_time)-7200, y= FairOddsH
      ),size= 3,color= 'firebrick')+
      scale_color_grey() + 
      theme_minimal() +   
      labs(y="Odds", x = "Scrape Time")+
      geom_vline(xintercept = as.numeric(short$date[1]-7200), col= 'grey')+
      scale_x_continuous(name= "Scrape Time", breaks= unixbreaks, 
                         labels= format(timebreaks,format= '%Y-%m-%d %H:%M'))+
      theme(axis.text.x = element_text(angle= 45))
    
    home_g <-ggplotly(home_plot, tooltip= 'text')%>%
      layout(annotations= 
               list(xref = "paper",
                    yref = "paper",
                    yanchor = "bottom",
                    xanchor = "center",
                    align = "center",
                    text = sprintf("<b>Home</b>"),
                    x = 0.5,
                    y = 1,
                    showarrow= F))
    
    
    draw_plot<-ggplot(short) +
      geom_line(aes(x=as.numeric(scrape_time)-7200, y=maxOddsD),size= 1, linetype= 'twodash',
                color= 'darkgreen')+
      geom_point(aes(x=as.numeric(scrape_time)-7200, y=maxOddsD,
                     text= paste("Max Bookie",substr(maxBookieD,1,nchar(maxBookieD)-1),
                                 "\n Max Odds: ", round(maxOddsD,4),
                                 "\n Fair Odds: ", round(FairOddsD,4),
                                 "\n Margin: ",glue("{round(MarginD*100,2)} %"),
                                 "\n Scrape Time: ", scrape_time
                                 
                     )
      ),size= 3,color= 'darkgreen')+
      geom_line(aes(x= as.numeric(scrape_time)-7200, y= FairOddsD), linetype= 'twodash',
                color= 'firebrick',
                size= 1)+
      geom_point(aes(x= as.numeric(scrape_time)-7200, y= FairOddsD
      ),size= 3,
      color= 'firebrick')+
      scale_color_grey() + 
      theme_minimal() +
      labs(y="Odds", x = "Scrape Time")+
      geom_vline(xintercept = as.numeric(short$date[1]-7200), col= 'grey')+
      scale_x_continuous(name= "Scrape Time", breaks= unixbreaks, 
                         labels= format(timebreaks,format= '%Y-%m-%d %H:%M'))+
      theme(axis.text.x = element_text(angle= 45)) 
    
    draw_g <-ggplotly(draw_plot, tooltip= 'text')%>%
      layout(annotations= 
               list(xref = "paper",
                    yref = "paper",
                    yanchor = "bottom",
                    xanchor = "center",
                    align = "center",
                    text = sprintf("<b>Draw</b>"),
                    x = 0.5,
                    y = 1,
                    showarrow= F))
    
    
    away_plot<-ggplot(short) +
      geom_line(aes(x=as.numeric(scrape_time)-7200, y=maxOddsA, color= 'Max Odds'),size= 1, linetype= 'twodash'
      )+
      geom_point(aes(x=as.numeric(scrape_time)-7200, y=maxOddsA, color= 'Max Odds',
                     text= paste("Max Bookie: ",substr(maxBookieA,1,nchar(maxBookieA)-1),
                                 "\n Max Odds: ", round(maxOddsA,4),
                                 "\n Fair Odds: ", round(FairOddsA,4),
                                 "\n Margin: ",glue("{round(MarginA*100,2)} %"),
                                 "\n Scrape Time: ", scrape_time
                     )
      ),size= 3)+
      geom_line(aes(x= as.numeric(scrape_time)-7200, y= FairOddsA,color= 'Fair Odds'), linetype= 'twodash',
                size= 1)+
      geom_point(aes(x= as.numeric(scrape_time)-7200, y= FairOddsA,color= 'Fair Odds'
      ),size= 3)+
      scale_color_grey() + 
      theme_minimal() +
      labs(y="Odds", x = "Scrape Time")+
      geom_vline(xintercept = as.numeric(short$date[1]-7200), col= 'grey')+
      scale_x_continuous(name= "Scrape Time", breaks= unixbreaks, 
                         labels= format(timebreaks,format= '%Y-%m-%d %H:%M'))+
      theme(axis.text.x = element_text(angle= 45)) +
      scale_color_manual(values = c(
        'Max Odds' = 'darkgreen',
        'Fair Odds' = 'firebrick'))+
      guides(color=guide_legend("")) 
    
    
    away_g <-ggplotly(away_plot, tooltip= 'text')%>%
      layout(annotations= 
               list(xref = "paper",
                    yref = "paper",
                    yanchor = "bottom",
                    xanchor = "center",
                    align = "center",
                    text = sprintf("<b>Away</b>"),
                    x = 0.5,
                    y = 1,
                    showarrow= F))
    
    
    return(subplot(home_g,draw_g,away_g, nrows = 1))
  }
  
  test_group1 = reactiveValues(df= get_data('test_group1'))

  test_group2 = reactiveValues(df= get_data('test_group2'))
  
  test_group3 = reactiveValues(df= get_data('test_group3'))
  
  test_group4 = reactiveValues(df= get_data('test_group4'))

  observeEvent(input$update,{
    test_group1$df= get_data('test_group1')
  })
  
  observeEvent(input$update,{
    test_group2$df= get_data('test_group2')
  })
  
  observeEvent(input$update,{
    test_group3$df= get_data('test_group3')
  })
  
  observeEvent(input$update,{
    test_group4$df= get_data('test_group4')
  })
  

  #fixtures = get_data('fixtures')
  
 
# here, I'll get the data based on input 
  data<- reactive({
    if (input$model== "Pinnacle Equal Margins"){
      data<-test_group1$df
      data}
    else if (input$model== "Pinnacle Proportional Margins"){
      data<-test_group2$df
      data
    }
    else if (input$model == "Consensus Equal Margins"){
      data<-test_group3$df
      data
    }
    else if (input$model == "Consensus Proportional Margins"){
      data<-test_group4$df
      data
    }
  })
 
  
  output$matches <- DT::renderDT(
    unique.data.frame(data()%>%
      select('home_team','away_team','date','country','league')
      ),filter= "top",
    selection = 'single',
    options = list(
        pageLength = 5
      )
    )
  
  observe({
    req(input$matches_cell_clicked >0)
    selRow<-data()[input$matches_cell_clicked$value,]
    if ("PinnacleSportsH" %in% colnames(data())){
      output$odds<- renderPlotly({panel_plots(selRow$home_team,selRow$away_team, selRow$date,data(),2)})}
    else{
      output$odds<- renderPlotly({panel_plots(selRow$home_team,selRow$away_team, selRow$date,data(),4)})}
  })
}
  

  
shinyApp(ui = ui, server = server)
  